from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from db import get_db
from schemas import ActressBasic, ActressFull, PageMeta, PageResult
from bson import ObjectId


router = APIRouter(prefix="/api/actresses", tags=["actresses"])


@router.get("", response_model=PageResult)
async def list_actresses(
    db: AsyncIOMotorDatabase = Depends(get_db),
    publisher: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="search in japan_name/roman_name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query("-movies_count"),
):
    q: Dict[str, Any] = {}
    if publisher:
        q["publisher"] = publisher
    if keyword:
        q["$or"] = [
            {"japan_name": {"$regex": keyword, "$options": "i"}},
            {"roman_name": {"$regex": keyword, "$options": "i"}},
        ]

    total = await db.actress.count_documents(q)
    cursor = db.actress.find(
        q,
        projection={
            "link": 1,
            "japan_name": 1,
            "roman_name": 1,
            "publisher": 1,
            "avatar": 1,
            "detail_parsed": 1,
            "movies": 1,
        },
    )

    # sort
    if sort:
        direction = DESCENDING if sort.startswith("-") else ASCENDING
        key = sort[1:] if sort.startswith("-") else sort
        if key == "movies_count":
            # sort client-side after fetch page slice (simple & efficient for now)
            pass
        else:
            cursor = cursor.sort(key, direction)

    cursor = cursor.skip((page - 1) * page_size).limit(page_size)
    docs: List[Dict[str, Any]] = await cursor.to_list(length=page_size)
    items: List[Dict[str, Any]] = []
    for d in docs:
        d["movies_count"] = len(d.get("movies", []))
        d.pop("movies", None)
        items.append(ActressBasic(**d).model_dump(by_alias=True))

    if sort and (sort.endswith("movies_count") or sort == "movies_count"):
        reverse = sort.startswith("-")
        items.sort(key=lambda x: x.get("movies_count", 0), reverse=reverse)

    return PageResult(
        items=items, meta=PageMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/{id}", response_model=ActressFull)
async def get_actress(id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = await db.actress.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Actress not found")
    # normalize
    if "movies" in doc and isinstance(doc["movies"], list):
        # clip large arrays for response size if necessary
        pass
    return ActressFull(**doc)
