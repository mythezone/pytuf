from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from db import get_db
from schemas import ActorSummary, ActorDoc, PageMeta, PageResult
from bson import ObjectId


router = APIRouter(prefix="/api/actresses", tags=["actresses"])


@router.get("", response_model=PageResult)
async def list_actresses(
    db: AsyncIOMotorDatabase = Depends(get_db),
    publisher: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="search in name/title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query("-movies_count"),
):
    q: Dict[str, Any] = {}
    if publisher:
        q["publisher"] = publisher
    if keyword:
        q["$or"] = [
            {"name": {"$regex": keyword, "$options": "i"}},
            {"title": {"$regex": keyword, "$options": "i"}},
        ]

    total = await db.actors.count_documents(q)
    cursor = db.actors.find(q)

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
        movies = d.get("movie_list")
        d["movies_count"] = len(movies) if isinstance(movies, list) else 0
        items.append(ActorSummary(**d).model_dump(by_alias=True))

    if sort and (sort.endswith("movies_count") or sort == "movies_count"):
        reverse = sort.startswith("-")
        items.sort(key=lambda x: x.get("movies_count", 0), reverse=reverse)

    return PageResult(
        items=items, meta=PageMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/random", response_model=ActorSummary)
async def random_actress(db: AsyncIOMotorDatabase = Depends(get_db)):
    pipeline = [
        {"$match": {"$and": [
            {"href": {"$exists": True}},
            {"movie_list": {"$exists": True, "$ne": []}},
        ]}},
        {"$sample": {"size": 1}},
        {"$project": {"href": 1, "name": 1, "title": 1, "avatar": 1, "category": 1, "movie_list": 1}},
    ]
    cur = db.actors.aggregate(pipeline)
    docs = await cur.to_list(length=1)
    if not docs:
        raise HTTPException(status_code=404, detail="No actress available")
    d = docs[0]
    d["movies_count"] = len(d.get("movie_list", []))
    return ActorSummary(**d)


@router.get("/{id}", response_model=ActorDoc)
async def get_actress(id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = await db.actors.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Actress not found")
    return ActorDoc(**doc)
