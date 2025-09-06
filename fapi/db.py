from __future__ import annotations

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin",
)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "jdb")


class Mongo:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


async def connect() -> None:
    if Mongo.client is None:
        Mongo.client = AsyncIOMotorClient(MONGO_URL)
        Mongo.db = Mongo.client[MONGO_DB_NAME]


async def disconnect() -> None:
    if Mongo.client is not None:
        Mongo.client.close()
        Mongo.client = None
        Mongo.db = None


def get_db() -> AsyncIOMotorDatabase:
    assert Mongo.db is not None, "MongoDB is not connected"
    return Mongo.db
