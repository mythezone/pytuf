from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


def _get_mysql_client():
    """Return a connected MySQL client (mysqlclient preferred).

    Tries `mysqlclient` (MySQLdb) first, then falls back to `pymysql` if
    available. The returned object must be API-compatible with MySQLdb.
    """

    # Connection settings with sensible defaults. Can be overridden via env.
    cfg = {
        "host": os.getenv("MYSQL_HOST", "10.16.12.105"),
        "port": int(os.getenv("MYSQL_PORT", "23306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "passwd": os.getenv("MYSQL_PASSWORD", "19891016Zmy!"),
        "db": os.getenv("MYSQL_DB", "movies"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "use_unicode": True,
    }

    try:  # Prefer mysqlclient
        import MySQLdb  # type: ignore
        from MySQLdb.cursors import DictCursor  # type: ignore

        conn = MySQLdb.connect(cursorclass=DictCursor, **cfg)
        return conn, DictCursor
    except Exception:
        # Optional fallback to pymysql for environments without mysqlclient
        try:
            import pymysql  # type: ignore

            pymysql.install_as_MySQLdb()
            from pymysql.cursors import DictCursor  # type: ignore

            conn = pymysql.connect(cursorclass=DictCursor, **cfg)
            return conn, DictCursor
        except Exception as exc:  # Re-raise with context
            raise RuntimeError(
                "Unable to import or connect using mysqlclient/pymysql"
            ) from exc


def _row_to_dict(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    # Normalize datetime/date/decimal to plain Python types
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


class MoviesMySQLClient:
    """Minimal client for reading legacy Django `movies` schema.

    Provides helpers to fetch one movie with its related actors and magnets.
    """

    def __init__(self) -> None:
        self._conn, self._dict_cursor = _get_mysql_client()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    # --- Core fetchers -------------------------------------------------
    def get_movie_by_id(self, movie_id: str) -> Optional[Dict[str, Any]]:
        """Fetch one movie by `movie_movie.id` with actors and magnets."""
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute(
                """
                SELECT m.*,
                       pub.id AS publisher_href, pub.name AS publisher_name,
                       dir.id AS director_href,  dir.name AS director_name,
                       mak.id AS maker_href,     mak.name AS maker_name
                FROM movie_movie AS m
                LEFT JOIN person_group AS pub ON m.publisher_id = pub.id
                LEFT JOIN person_group AS dir ON m.director_id  = dir.id
                LEFT JOIN person_group AS mak ON m.maker_id     = mak.id
                WHERE m.id = %s
                LIMIT 1
                """,
                (movie_id,),
            )
            movie_row = cur.fetchone()

        if not movie_row:
            return None

        # Actors
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute(
                """
                SELECT pg.id, pg.name, pg.avatar, pg.role
                FROM movie_movie_actors mma
                JOIN person_group pg ON mma.group_id = pg.id
                WHERE mma.movie_id = %s
                ORDER BY pg.name ASC
                """,
                (movie_id,),
            )
            actors: List[Dict[str, Any]] = [
                _row_to_dict(r) or {} for r in cur.fetchall() or []
            ]

        # Tags
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute(
                """
                SELECT pg.id, pg.name, pg.avatar, pg.role
                FROM movie_movie_tags mmt
                JOIN person_group pg ON mmt.group_id = pg.id
                WHERE mmt.movie_id = %s
                ORDER BY pg.name ASC
                """,
                (movie_id,),
            )
            tags: List[Dict[str, Any]] = [
                _row_to_dict(r) or {} for r in cur.fetchall() or []
            ]

        # Magnets
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute(
                """
                SELECT id, name, meta, tags, time
                FROM movie_magnet
                WHERE movie_id = %s
                ORDER BY time DESC, id DESC
                """,
                (movie_id,),
            )
            magnets: List[Dict[str, Any]] = [
                _row_to_dict(r) or {} for r in cur.fetchall() or []
            ]

        # Recommendations (may_like)
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute(
                """
                SELECT dest.id AS href,
                       dest.code AS code,
                       COALESCE(dest.current_title, dest.origin_title, '') AS title,
                       dest.cover AS cover
                FROM movie_movie_may_like AS ml
                JOIN movie_movie AS dest ON dest.id = ml.to_movie_id
                WHERE ml.from_movie_id = %s
                ORDER BY dest.release_date DESC, dest.id DESC
                """,
                (movie_id,),
            )
            recs: List[Dict[str, Any]] = [
                _row_to_dict(r) or {} for r in cur.fetchall() or []
            ]

        # Transform to Mongo-style keys
        m = _row_to_dict(movie_row) or {}

        def parse_tags_field(s: Any) -> List[str]:
            if not s:
                return []
            if isinstance(s, list):
                return s
            try:
                import json
                return json.loads(s)
            except Exception:
                txt = str(s).strip().strip("[]")
                return [p.strip().strip("'\"") for p in txt.split(",") if p.strip()]

        result: Dict[str, Any] = {
            "href": m.get("id"),
            "code": (m.get("code") or "").strip(),
            "cover": m.get("cover") or "",
            "publish_date": m.get("release_date"),
            "rater": m.get("rater", 0),
            "rating": m.get("rate", 0),
            "title": (m.get("current_title") or m.get("origin_title") or "").strip(),
            "duration_minutes": m.get("duration"),
            "video_src": m.get("video_src"),
        }

        if m.get("publisher_href"):
            result["publisher"] = {
                "name": m.get("publisher_name") or "",
                "href": m.get("publisher_href"),
            }
        if m.get("director_href"):
            result["director"] = {
                "name": m.get("director_name") or "",
                "href": m.get("director_href"),
            }
        if m.get("maker_href"):
            result["maker"] = {
                "name": m.get("maker_name") or "",
                "href": m.get("maker_href"),
            }

        # Map actors: id -> href, drop role/avatar
        result["actors"] = [
            {"name": a.get("name", ""), "href": a.get("id")}
            for a in actors
            if a.get("id")
        ]

        # Categories from tags; also provide plain tag names
        result["categories"] = [
            {"name": t.get("name", ""), "href": t.get("id")}
            for t in tags
            if t.get("id")
        ]
        result["tags"] = [t.get("name", "") for t in tags if t.get("name")]

        # Magnets key normalization
        result["magnets"] = [
            {
                "magnet": mg.get("id"),
                "name": mg.get("name"),
                "meta_text": mg.get("meta"),
                "tags": parse_tags_field(mg.get("tags")),
                "date": mg.get("time"),
            }
            for mg in magnets
            if mg.get("id")
        ]

        # Recommendations mapped to expected fields
        result["recommendations"] = [
            {
                "id": (r.get("code") or "").strip(),
                "title": r.get("title") or "",
                "cover": r.get("cover") or "",
                "href": r.get("href"),
            }
            for r in recs
            if r.get("href")
        ]

        return result

    # --- Mongo Upsert --------------------------------------------------
    def upsert_to_mongo(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert the transformed doc into MongoDB `jdb.movies`.

        Merge rules:
        - Local cover (not starting with https) never overwritten.
        - Merge arrays by unique keys: actors/categories by href, magnets by magnet, tags by string.
        - Prefer adding information; do not overwrite existing non-empty scalars.
        """
        # Lazy import to avoid hard dependency when only using MySQL features
        try:
            from pymongo import MongoClient  # type: ignore
        except Exception as exc:
            raise RuntimeError("pymongo is required for Mongo upsert") from exc

        from fapi.db import MONGO_URL, MONGO_DB_NAME  # reuse existing settings

        client = MongoClient(MONGO_URL)
        db = client[MONGO_DB_NAME]
        col = db["movies"]

        href = doc.get("href")
        assert href, "document must contain href"

        existing = col.find_one({"href": href})

        def merge_scalar(key: str):
            val = doc.get(key)
            if val is None or val == "" or val == 0:
                return
            if not existing or existing.get(key) in (None, "", 0):
                upd[key] = val

        upd: Dict[str, Any] = {}

        # Cover rule
        if doc.get("cover"):
            if not existing or not existing.get("cover") or str(existing.get("cover")).startswith("http"):
                # Existing cover is remote or missing; allow overwrite
                upd["cover"] = doc["cover"]

        # Simple scalars
        for k in [
            "code",
            "publish_date",
            "rater",
            "rating",
            "title",
            "duration_minutes",
            "video_src",
        ]:
            merge_scalar(k)

        # Merge nested single objects
        def merge_object(key: str):
            obj = doc.get(key)
            if not obj:
                return
            current = (existing or {}).get(key) or {}
            merged = {**current}
            if not current.get("href") and obj.get("href"):
                merged["href"] = obj.get("href")
            if not current.get("name") and obj.get("name"):
                merged["name"] = obj.get("name")
            if merged != current:
                upd[key] = merged

        for key in ("publisher", "director", "maker"):
            merge_object(key)

        # Merge arrays
        def merge_by_key(arr_key: str, item_key: str):
            new_items = doc.get(arr_key) or []
            if not new_items:
                return
            curr = list((existing or {}).get(arr_key) or [])
            seen = {item.get(item_key): i for i, item in enumerate(curr) if item.get(item_key)}
            changed = False
            for item in new_items:
                k = item.get(item_key)
                if not k or k in seen:
                    continue
                curr.append(item)
                seen[k] = len(curr) - 1
                changed = True
            if changed:
                upd[arr_key] = curr

        merge_by_key("actors", "href")
        merge_by_key("categories", "href")
        merge_by_key("magnets", "magnet")

        # tags is list[str]
        if doc.get("tags"):
            curr_tags = set((existing or {}).get("tags") or [])
            new_tags = set(doc["tags"]) - curr_tags
            if new_tags:
                upd["tags"] = list(curr_tags | new_tags)

        # recommendations: by href
        merge_by_key("recommendations", "href")

        if not existing:
            to_insert = {**doc}
            if upd:
                to_insert.update(upd)
            col.insert_one(to_insert)
            result = to_insert
        else:
            if upd:
                col.update_one({"_id": existing["_id"]}, {"$set": upd})
                existing.update(upd)
            result = existing

        return result

    def transfer_movie_by_id(self, movie_id: str) -> Dict[str, Any]:
        """Fetch from MySQL, upsert into Mongo, and mark as transferred."""
        doc = self.get_movie_by_id(movie_id)
        assert doc is not None, f"movie not found: {movie_id}"
        saved = self.upsert_to_mongo(doc)

        # Mark as transferred on MySQL side
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE movie_movie SET transfered = 1 WHERE id = %s",
                    (movie_id,),
                )
            self._conn.commit()
        except Exception:
            # If column doesn't exist, ignore silently
            self._conn.rollback()

        return saved

    def get_movie_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Fetch one movie by `movie_movie.code` (exact match)."""
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute(
                "SELECT id FROM movie_movie WHERE code = %s LIMIT 1",
                (code,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return self.get_movie_by_id(row["id"])  # type: ignore[index]

    def get_all_movies(self) -> List[Dict[str, Any]]:
        """Fetch all movies in the database."""
        with self._conn.cursor(self._dict_cursor) as cur:
            cur.execute("SELECT * FROM movie_movie LIMIT 10")
            rows = cur.fetchall()
        return rows if rows else []


__all__ = ["MoviesMySQLClient"]
