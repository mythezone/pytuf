from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId as _ObjectId


class PyObjectId(_ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        if isinstance(v, _ObjectId):
            return v
        try:
            return _ObjectId(str(v))
        except Exception as e:
            raise ValueError("Invalid ObjectId") from e


class MongoModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = { _ObjectId: str }


# ---------- New Movie/Actor Schemas matching current Mongo ----------

class NameHref(BaseModel):
    name: Optional[str] = None
    href: Optional[str] = None


class ActorRef(BaseModel):
    name: Optional[str] = None
    href: Optional[str] = None
    gender: Optional[str] = None


class CategoryRef(BaseModel):
    name: Optional[str] = None
    href: Optional[str] = None


class RecommendationRef(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    cover: Optional[str] = None
    href: Optional[str] = None


class VideoInfo(BaseModel):
    root: Optional[str] = None
    path: Optional[str] = None
    abs_path: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_seconds: Optional[Union[float, None]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None


class MovieDoc(MongoModel):
    href: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    cover: Optional[str] = None
    cover_full: Optional[str] = None
    publish_date: Optional[str] = None
    rater: Optional[Union[int, None]] = None
    rating: Optional[Union[float, None]] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    actors: Optional[List[ActorRef]] = None
    categories: Optional[List[CategoryRef]] = None
    detail_parsed: Optional[bool] = None
    detail_parsed_at: Optional[Union[str, datetime]] = None
    duration_minutes: Optional[int] = None
    duration_text: Optional[str] = None
    magnets: Optional[List[Dict[str, Any]]] = None
    maker: Optional[NameHref] = None
    publisher: Optional[NameHref] = None
    recommendations: Optional[List[RecommendationRef]] = None
    related_lists: Optional[List[Dict[str, Any]]] = None
    reviews: Optional[List[Dict[str, Any]]] = None
    screenshots: Optional[List[str]] = None
    video: Optional[VideoInfo] = None
    series: Optional[Any] = None


class MovieSummary(MongoModel):
    href: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    cover: Optional[str] = None
    publish_date: Optional[str] = None
    rating: Optional[Union[float, None]] = None
    rater: Optional[Union[int, None]] = None
    tags: Optional[List[str]] = None


class ActorMovieMini(BaseModel):
    title: Optional[str] = None
    href: Optional[str] = None
    cover: Optional[str] = None
    id: Optional[str] = None
    mongo_id: Optional[str] = None


class ActorDoc(MongoModel):
    href: Optional[str] = None
    avatar: Optional[Union[str, bool]] = None
    name: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    last_stats: Optional[Dict[str, Any]] = None
    movie_list: Optional[List[ActorMovieMini]] = None
    movie_list_parsed: Optional[bool] = None
    movie_list_parsed_at: Optional[Union[str, datetime]] = None
    tags: Optional[List[str]] = None


class ActorSummary(MongoModel):
    href: Optional[str] = None
    avatar: Optional[Union[str, bool]] = None
    name: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    movies_count: Optional[int] = None


# Pagination
class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PageResult(BaseModel):
    items: List[Dict[str, Any]]
    meta: PageMeta


# Graph
class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    data: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "acted_in"


class GraphResult(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    meta: Dict[str, Any] = {}
