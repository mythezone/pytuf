from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId as _ObjectId


class PyObjectId(_ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
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


# Actress
class ActressBasic(MongoModel):
    link: Optional[str] = None
    japan_name: Optional[str] = None
    roman_name: Optional[str] = None
    publisher: Optional[str] = None
    avatar: Optional[str] = None
    detail_parsed: Optional[bool] = None
    movies_count: Optional[int] = None


class ActressFull(ActressBasic):
    profile: Optional[Dict[str, Any]] = None
    movies: Optional[List[Dict[str, Any]]] = None
    movies_parsed: Optional[bool] = None
    profile_parsed: Optional[bool] = None
    avatar_parsed: Optional[bool] = None


# Movie
class MovieBasic(MongoModel):
    title: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    publisher: Optional[str] = None
    link: Optional[str] = None


class MovieFull(MovieBasic):
    profile: Optional[Dict[str, Any]] = None
    screenshots: Optional[List[str]] = None
    image_parsed: Optional[bool] = None
    profile_parsed: Optional[bool] = None


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

