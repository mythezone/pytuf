from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from db import get_db
from schemas import GraphEdge, GraphNode, GraphResult


router = APIRouter(prefix="/api/graph", tags=["graph"])


def node_id(kind: str, oid: ObjectId | str) -> str:
    return f"{kind}:{str(oid)}"


def mk_actor_node(doc: Dict[str, Any]) -> GraphNode:
    label = doc.get("name") or doc.get("title") or "Actress"
    return GraphNode(
        id=node_id("a", doc["_id"]),
        type="actress",
        label=label,
        data={
            "avatar": doc.get("avatar"),
            "category": doc.get("category"),
            "href": doc.get("href"),
        },
    )


def mk_movie_node(doc: Dict[str, Any]) -> GraphNode:
    label = doc.get("code") or (doc.get("title") or "Movie")
    data = {
        "title": doc.get("title"),
        "code": doc.get("code"),
        "cover": doc.get("cover"),
        "href": doc.get("href"),
    }
    # 如果有本地视频，带上 video 字段
    if doc.get("video"):
        data["video"] = True
    return GraphNode(
        id=node_id("m", doc["_id"]),
        type="movie",
        label=label,
        data=data,
    )


@router.get("/actress/{id}", response_model=GraphResult)
async def graph_by_actress(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

    actress = await db.actors.find_one({"_id": oid})
    if not actress:
        raise HTTPException(status_code=404, detail="Actress not found")

    nodes: List[GraphNode] = [mk_actor_node(actress)]
    edges: List[GraphEdge] = []

    movie_ids: List[ObjectId] = []
    movies_src = list((actress.get("movie_list") or []))
    # 随机抽样以控制返回规模
    if len(movies_src) > limit:
        movies_src = random.sample(movies_src, limit)
    for m in movies_src:
        mid = m.get("mongo_id")
        try:
            movie_ids.append(ObjectId(str(mid)))
        except Exception:
            continue

    if movie_ids:
        cursor = db.movies.find(
            {"_id": {"$in": movie_ids}},
            projection={"title": 1, "code": 1, "cover": 1, "href": 1},
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
async def graph_by_movie(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

    movie = await db.movies.find_one({"_id": oid})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    nodes: List[GraphNode] = [mk_movie_node(movie)]
    edges: List[GraphEdge] = []

    # 从 movie.actors 通过 href 匹配演员
    actress_nodes: Dict[str, GraphNode] = {}
    hrefs: List[str] = []
    actors_src = list((movie.get("actors") or []))
    if len(actors_src) > limit:
        actors_src = random.sample(actors_src, limit)
    for a in actors_src:
        if isinstance(a, dict) and a.get("href"):
            hrefs.append(a["href"])
    if hrefs:
        cursor = db.actors.find({"href": {"$in": hrefs}})
        actresses = await cursor.to_list(length=200)
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
    ac = db.actors.find(
        {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"title": {"$regex": keyword, "$options": "i"}},
            ]
        },
        projection={"name": 1, "title": 1, "avatar": 1, "category": 1, "href": 1},
    )
    actresses = await ac.to_list(length=limit)
    for a in actresses:
        nodes.append(mk_actor_node(a))

    # movies
    mc = db.movies.find(
        {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"code": {"$regex": keyword, "$options": "i"}},
            ]
        },
        projection={"title": 1, "code": 1, "cover": 1, "href": 1},
    )
    movies = await mc.to_list(length=limit)
    for m in movies:
        nodes.append(mk_movie_node(m))

    return GraphResult(
        nodes=nodes,
        edges=edges,
        meta={"actresses": len(actresses), "movies": len(movies)},
    )
