from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from db import get_db
from schemas import MovieSummary, MovieDoc, PageMeta, PageResult


router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=PageResult)
async def list_movies(
    db: AsyncIOMotorDatabase = Depends(get_db),
    publisher: Optional[str] = Query(None),
    keyword: Optional[str] = Query(
        None, description="search in title/description/code"
    ),
    code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query("-profile_parsed"),
):
    q: Dict[str, Any] = {}
    if publisher:
        q["publisher"] = publisher
    if code:
        q["code"] = code
    if keyword:
        q["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
            {"code": {"$regex": keyword, "$options": "i"}},
        ]

    total = await db.movies.count_documents(q)
    cursor = db.movies.find(q)
    if sort:
        direction = DESCENDING if sort.startswith("-") else ASCENDING
        key = sort[1:] if sort.startswith("-") else sort
        cursor = cursor.sort(key, direction)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)
    docs = await cursor.to_list(length=page_size)
    items = [MovieSummary(**d).model_dump(by_alias=True) for d in docs]
    return PageResult(
        items=items, meta=PageMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/random", response_model=MovieSummary)
async def random_movie(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Pick a random movie with a two-pass strategy:
    1) Prefer parsed or media-present movies
    2) Fallback to any document having an href
    """
    strict_match = {
        "$and": [
            {"href": {"$exists": True}},
            {"$or": [
                {"detail_parsed": True},
                {"screenshots.0": {"$exists": True}},
                {"cover": {"$type": "string", "$ne": ""}},
            ]},
        ]
    }
    fallback_match = {"href": {"$exists": True}}

    async def _one(match: Dict[str, Any]):
        cur = db.movies.aggregate([
            {"$match": match},
            {"$sample": {"size": 1}},
            {"$project": {"title": 1, "code": 1, "href": 1, "cover": 1, "publish_date": 1, "rating": 1, "rater": 1, "tags": 1}},
        ])
        docs = await cur.to_list(length=1)
        return docs[0] if docs else None

    doc = await _one(strict_match)
    if not doc:
        doc = await _one(fallback_match)
    if not doc:
        raise HTTPException(status_code=404, detail="No movie available")
    return MovieSummary(**doc)


@router.get("/{id}", response_model=MovieDoc)
async def get_movie(id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = await db.movies.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Movie not found")
    return MovieDoc(**doc)
