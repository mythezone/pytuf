from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from db import get_db
from schemas import GraphEdge, GraphNode, GraphResult


router = APIRouter(prefix="/api/graph", tags=["graph"])


def node_id(kind: str, oid: ObjectId | str) -> str:
    return f"{kind}:{str(oid)}"


def mk_actor_node(doc: Dict[str, Any]) -> GraphNode:
    label = doc.get("japan_name") or doc.get("roman_name") or "Actress"
    return GraphNode(
        id=node_id("a", doc["_id"]),
        type="actress",
        label=label,
        data={
            "publisher": doc.get("publisher"),
            "avatar": doc.get("avatar"),
        },
    )


def mk_movie_node(doc: Dict[str, Any]) -> GraphNode:
    label = doc.get("code") or (doc.get("title") or "Movie")
    return GraphNode(
        id=node_id("m", doc["_id"]),
        type="movie",
        label=label,
        data={
            "title": doc.get("title"),
            "publisher": doc.get("publisher"),
            "code": doc.get("code"),
        },
    )


@router.get("/actress/{id}", response_model=GraphResult)
async def graph_by_actress(id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

    actress = await db.actress.find_one({"_id": oid})
    if not actress:
        raise HTTPException(status_code=404, detail="Actress not found")

    nodes: List[GraphNode] = [mk_actor_node(actress)]
    edges: List[GraphEdge] = []

    movie_ids: List[ObjectId] = []
    for m in actress.get("movies", []) or []:
        mid = m.get("id")
        try:
            movie_ids.append(ObjectId(mid))
        except Exception:
            continue

    if movie_ids:
        cursor = db.movie.find(
            {"_id": {"$in": movie_ids}},
            projection={"title": 1, "code": 1, "publisher": 1},
        )
        movies = await cursor.to_list(length=1000)
        for md in movies:
            mn = mk_movie_node(md)
            nodes.append(mn)
            edges.append(
                GraphEdge(
                    id=f"e:{actress['_id']}:{md['_id']}",
                    source=node_id("a", actress["_id"]),
                    target=mn.id,
                )
            )

    return GraphResult(
        nodes=nodes,
        edges=edges,
        meta={"actress": str(actress["_id"]), "movie_count": len(movie_ids)},
    )


@router.get("/movie/{id}", response_model=GraphResult)
async def graph_by_movie(id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

    movie = await db.movie.find_one({"_id": oid})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    nodes: List[GraphNode] = [mk_movie_node(movie)]
    edges: List[GraphEdge] = []

    # 尝试从 profile['女優'] 匹配演员
    names: List[str] = []
    prof = movie.get("profile") or {}
    cast = prof.get("女優") or prof.get("女優 ") or []
    if isinstance(cast, list):
        names = [str(x) for x in cast]
    elif isinstance(cast, str) and cast.strip():
        names = [cast.strip()]

    actress_nodes: Dict[str, GraphNode] = {}
    if names:
        cursor = db.actress.find(
            {
                "$or": [
                    {"japan_name": {"$in": names}},
                    {"roman_name": {"$in": names}},
                ]
            },
            projection={"japan_name": 1, "roman_name": 1, "publisher": 1, "avatar": 1},
        )
        actresses = await cursor.to_list(length=100)
        for ad in actresses:
            an = mk_actor_node(ad)
            actress_nodes[str(ad["_id"])] = an
            nodes.append(an)
            edges.append(
                GraphEdge(
                    id=f"e:{ad['_id']}:{movie['_id']}",
                    source=an.id,
                    target=node_id("m", movie["_id"]),
                )
            )

    return GraphResult(
        nodes=nodes,
        edges=edges,
        meta={"movie": str(movie["_id"]), "actress_count": len(actress_nodes)},
    )


@router.get("/search", response_model=GraphResult)
async def graph_search(
    db: AsyncIOMotorDatabase = Depends(get_db),
    keyword: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

    # actresses
    ac = db.actress.find(
        {
            "$or": [
                {"japan_name": {"$regex": keyword, "$options": "i"}},
                {"roman_name": {"$regex": keyword, "$options": "i"}},
            ]
        },
        projection={"japan_name": 1, "roman_name": 1, "publisher": 1, "avatar": 1},
    )
    actresses = await ac.to_list(length=limit)
    for a in actresses:
        nodes.append(mk_actor_node(a))

    # movies
    mc = db.movie.find(
        {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}},
                {"code": {"$regex": keyword, "$options": "i"}},
            ]
        },
        projection={"title": 1, "code": 1, "publisher": 1},
    )
    movies = await mc.to_list(length=limit)
    for m in movies:
        nodes.append(mk_movie_node(m))

    return GraphResult(
        nodes=nodes,
        edges=edges,
        meta={"actresses": len(actresses), "movies": len(movies)},
    )
