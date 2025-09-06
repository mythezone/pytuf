from __future__ import annotations

from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from typing import Any, Dict
import time as _t
import re

from base import BaseScraper, MongoDB
from clawer import parse_video_detail_html, base_url


class MovieScraper(BaseScraper):
    def __init__(self, movie_href: str):
        super().__init__()
        abs_url = urljoin(base_url, movie_href)
        self.movie_url = abs_url
        self.movie_path = urlparse(abs_url).path  # e.g. /v/xxxx
        self.db = MongoDB()
        self.movies_col = "movies"

    # ---------- merge helpers (consistent with actor.py) ----------
    def _merge_values(self, a, b):
        return b if (a is None or a == "" or a == []) else a

    def _merge_lists(self, a_list, b_list):
        if not isinstance(a_list, list):
            return b_list if isinstance(b_list, list) else a_list
        if not isinstance(b_list, list):
            return a_list

        def key_of(x):
            if isinstance(x, dict):
                return x.get("href") or x.get("id") or repr(sorted(x.items()))
            return x

        seen = set()
        out = []
        for src in (a_list, b_list):
            for it in src:
                k = key_of(it)
                if k in seen:
                    continue
                seen.add(k)
                out.append(it)
        return out

    def _merge_docs(self, target: dict, source: dict) -> dict:
        merged = dict(target)
        for k, v in source.items():
            if k == "_id":
                continue
            tv = merged.get(k)
            if isinstance(tv, list) or isinstance(v, list):
                merged[k] = self._merge_lists(
                    tv if isinstance(tv, list) else [], v if isinstance(v, list) else []
                )
            elif isinstance(tv, dict) and isinstance(v, dict):
                mv = dict(tv)
                for kk, vv in v.items():
                    if kk == "_id":
                        continue
                    mv[kk] = self._merge_values(mv.get(kk), vv)
                merged[k] = mv
            else:
                merged[k] = self._merge_values(tv, v)
        return merged

    def _normalize_href(self, path: str) -> None:
        col = self.db.db[self.movies_col]
        rel = col.find_one({"href": path})
        abs_doc = col.find_one(
            {"href": {"$regex": f"^https?://[^/]+{re.escape(path)}$"}}
        )
        if abs_doc and not rel:
            col.update_one({"_id": abs_doc["_id"]}, {"$set": {"href": path}})
            return
        if abs_doc and rel and abs_doc["_id"] != rel["_id"]:
            merged = self._merge_docs(rel, abs_doc)
            col.update_one({"_id": rel["_id"]}, {"$set": merged})
            col.delete_one({"_id": abs_doc["_id"]})

    # ---------- main ----------
    def run(self) -> dict:
        # fetch page
        self.init(self.movie_url)
        if not self.soup:
            return {"ok": False, "error": "fetch_failed"}

        detail = parse_video_detail_html(str(self.soup)).to_dict()
        # derive tags from categories + magnet tags
        cat_list = detail.get("categories") or []
        tags_set = set()
        for c in cat_list:
            name = (c or {}).get("name")
            if name:
                tags_set.add(name)
        for m in (detail.get("magnets") or []):
            for t in (m or {}).get("tags", []) or []:
                if t:
                    tags_set.add(t)
        tags = list(tags_set)

        update_doc: Dict[str, Any] = {
            "title": detail.get("title"),
            "code": detail.get("code"),
            "href": self.movie_path,
            "cover": detail.get("cover") or detail.get("cover_full"),
            "cover_full": detail.get("cover_full"),
            "screenshots": detail.get("screenshots") or [],
            "publish_date": detail.get("date"),
            "duration_minutes": detail.get("duration_minutes"),
            "duration_text": detail.get("duration_text"),
            "maker": detail.get("maker"),
            "publisher": detail.get("publisher"),
            "series": detail.get("series"),
            "categories": detail.get("categories") or [],
            "tags": tags,
            "actors": detail.get("actors") or [],
            "rating": detail.get("rating"),
            "rater": detail.get("rating_count"),
            "magnets": detail.get("magnets") or [],
            "reviews": detail.get("reviews") or [],
            "related_lists": detail.get("related_lists") or [],
            "recommendations": detail.get("recommendations") or [],
            "source": "javdb",
            "detail_parsed": True,
            "detail_parsed_at": datetime.now(timezone.utc),
        }

        self._normalize_href(self.movie_path)
        res = self.db.db[self.movies_col].update_one(
            {"href": self.movie_path}, {"$set": update_doc}, upsert=True
        )
        upserted = bool(res.upserted_id)
        return {"ok": True, "upserted": upserted}


if __name__ == "__main__":
    import sys

    db = MongoDB()
    col = db.db["movies"]

    # compute total at start
    total = col.count_documents(
        {"detail_parsed": {"$ne": True}, "href": {"$exists": True}}
    )
    processed = 0

    def draw_progress(processed: int, total: int, current: str = ""):
        width = 30
        ratio = (processed / total) if total > 0 else 0
        filled = int(width * ratio)
        bar = "█" * filled + "─" * (width - filled)
        pct = ratio * 100.0
        line = f"[{bar}] {processed}/{total} ({pct:.1f}%)  current: {current}"
        sys.stdout.write("\r" + line[:120])  # limit width
        sys.stdout.flush()

    def wait_progress(seconds: int, label: str = "wait") -> None:
        width = 30
        start = _t.time()
        while True:
            el = _t.time() - start
            if el > seconds:
                el = seconds
            ratio = el / seconds if seconds > 0 else 1
            filled = int(width * ratio)
            bar = "█" * filled + "─" * (width - filled)
            pct = ratio * 100
            remaining = max(0, int(seconds - el))
            sys.stdout.write(
                "\r" + f"[{bar}] {pct:5.1f}% | {label} {remaining:2d}s"[:120]
            )
            sys.stdout.flush()
            if el >= seconds:
                break
            _t.sleep(0.1)
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    while True:
        sample = list(
            col.aggregate(
                [
                    {
                        "$match": {
                            "detail_parsed": {"$ne": True},
                            "href": {"$exists": True},
                        }
                    },
                    {"$sample": {"size": 1}},
                ]
            )
        )
        if not sample:
            # idle waiting with progress bar
            wait_progress(20, label="idle")
            # refresh total snapshot as tasks may arrive later
            total = col.count_documents(
                {"detail_parsed": {"$ne": True}, "href": {"$exists": True}}
            )
            continue

        doc = sample[0]
        href = doc.get("href") or ""
        draw_progress(processed, total, current=href)
        try:
            ms = MovieScraper(href)
            result = ms.run()
            if result.get("ok"):
                col.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "detail_parsed": True,
                            "detail_parsed_at": datetime.now(timezone.utc),
                        }
                    },
                )
                processed += 1
                draw_progress(processed, total, current=href)
            else:
                col.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "detail_parse_error": result.get("error"),
                            "detail_parsed": False,
                            "detail_error_at": datetime.now(timezone.utc),
                        }
                    },
                )
        except Exception as e:
            col.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "detail_parse_error": str(e),
                        "detail_parsed": False,
                        "detail_error_at": datetime.now(timezone.utc),
                    }
                },
            )

        # cooldown wait with progress bar
        wait_progress(2, label="cooldown")
