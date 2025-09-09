from __future__ import annotations

import mimetypes
import os
import re
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from db import get_db


router = APIRouter(prefix="/video", tags=["video"])


def _canon(code: str) -> Tuple[str, str]:
    s = re.sub(r"[^0-9A-Za-z]", "", code.upper())
    letters = []
    rest = []
    hit_digit = False
    for ch in s:
        if not hit_digit and ch.isalpha():
            letters.append(ch)
        else:
            hit_digit = True
            rest.append(ch)
    return ("".join(letters), "".join(rest))


def _parse_range(range_header: Optional[str], file_size: int) -> Optional[tuple[int, int]]:
    if not range_header:
        return None
    try:
        units, rng = range_header.split("=", 1)
        if units.strip().lower() != "bytes":
            return None
        start_s, end_s = (rng.split("-", 1) + [""])[:2]
        if start_s == "":
            length = int(end_s)
            if length <= 0:
                return None
            start = max(0, file_size - length)
            end = file_size - 1
        else:
            start = int(start_s)
            end = int(end_s) if end_s else file_size - 1
        if start > end or start >= file_size:
            return None
        end = min(end, file_size - 1)
        return start, end
    except Exception:
        return None


@router.get("/{code}")
async def serve_video(code: str, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)) -> Response:
    letters, digits = _canon(code)
    if not letters or not digits:
        raise HTTPException(status_code=400, detail="Invalid code")
    pattern = f"^{re.escape(letters)}[- ]?{re.escape(digits)}$"
    doc: Dict[str, Any] | None = await db.movies.find_one({"code": {"$regex": pattern, "$options": "i"}},
                                                          projection={"video": 1, "code": 1})
    if not doc or not doc.get("video"):
        raise HTTPException(status_code=404, detail="Video not found")
    v = doc["video"]
    full_path = v.get("abs_path") or os.path.join(v.get("root", ""), v.get("path", ""))
    if not full_path or not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File missing")

    st = os.stat(full_path)
    file_size = st.st_size
    range_header = request.headers.get("range")
    byte_range = _parse_range(range_header, file_size)
    ctype, _ = mimetypes.guess_type(full_path)
    ctype = ctype or "video/mp4"

    def file_iterator(start: int, end: int, chunk_size: int = 1024 * 1024):
        with open(full_path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers = {"Accept-Ranges": "bytes"}
    if byte_range is None:
        return StreamingResponse(file_iterator(0, file_size - 1), media_type=ctype,
                                 headers={**headers, "Content-Length": str(file_size)})

    start, end = byte_range
    content_length = end - start + 1
    headers.update({"Content-Range": f"bytes {start}-{end}/{file_size}", "Content-Length": str(content_length)})
    return StreamingResponse(file_iterator(start, end), media_type=ctype, headers=headers, status_code=206)

