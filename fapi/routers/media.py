from __future__ import annotations

import os
import mimetypes
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

os.environ["MEDIA_ROOT"] = "/Volumes/images/jdb"

MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/Volumes/images/jdb")

router = APIRouter(prefix="/media", tags=["media"])


def _safe_path(rel_path: str) -> str:
    rel_path = rel_path.lstrip("/\\")
    full = os.path.realpath(os.path.join(MEDIA_ROOT, rel_path))
    root = os.path.realpath(MEDIA_ROOT)
    if not full.startswith(root + os.sep) and full != root:
        raise HTTPException(status_code=403, detail="Forbidden")
    return full


def _file_etag(st: os.stat_result) -> str:
    # inode-mtime-size as weak ETag surrogate
    return f'W/"{st.st_ino:x}-{st.st_mtime_ns:x}-{st.st_size:x}"'


def _http_date(ts: float) -> str:
    return formatdate(ts, usegmt=True)


def _parse_range(
    range_header: Optional[str], file_size: int
) -> Optional[tuple[int, int]]:
    if not range_header:
        return None
    try:
        units, rng = range_header.split("=", 1)
        if units.strip().lower() != "bytes":
            return None
        start_s, end_s = (rng.split("-", 1) + [""])[:2]
        if start_s == "":
            # suffix range: bytes=-N
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


@router.head("/{path:path}")
@router.get("/{path:path}")
def serve_media(path: str, request: Request) -> Response:
    full_path = _safe_path(path)
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Not Found")

    st = os.stat(full_path)
    etag = _file_etag(st)
    last_modified = _http_date(st.st_mtime)

    # Conditional requests
    inm = request.headers.get("if-none-match")
    if inm and inm == etag:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )

    range_header = request.headers.get("range")
    file_size = st.st_size
    byte_range = _parse_range(range_header, file_size)

    ctype, _ = mimetypes.guess_type(full_path)
    ctype = ctype or "application/octet-stream"

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

    headers = {
        "Accept-Ranges": "bytes",
        "ETag": etag,
        "Last-Modified": last_modified,
        "Cache-Control": "public, max-age=31536000, immutable",
    }

    if byte_range is None:
        if request.method == "HEAD":
            return Response(
                status_code=200,
                headers={
                    **headers,
                    "Content-Length": str(file_size),
                    "Content-Type": ctype,
                },
            )
        return StreamingResponse(
            file_iterator(0, file_size - 1),
            media_type=ctype,
            headers={**headers, "Content-Length": str(file_size)},
        )

    start, end = byte_range
    content_length = end - start + 1
    headers.update(
        {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
        }
    )
    status = 206
    if request.method == "HEAD":
        return Response(status_code=status, headers={**headers, "Content-Type": ctype})
    return StreamingResponse(
        file_iterator(start, end), media_type=ctype, headers=headers, status_code=status
    )
