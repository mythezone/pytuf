from __future__ import annotations

"""
Merge movie data from `myj.movies` into `jdb.movies` by code.

Matching
- myj codes may omit the hyphen and even prepend a label prefix (e.g. 'DVDONSD340').
- jdb codes look like 'ONSD-340'.
- We normalize both sides and also build a fallback key using the last up-to-4
  letters plus the numeric part so that 'DVDONSD340' matches 'ONSD-340'.

Updates
- screenshots  -> screenshots2   (set/overwrite)
- profile      -> profile        (set/overwrite)
- link         -> link           (set/overwrite)
- description  -> description    (set/overwrite)
- publisher    -> publisher      (only when target missing or null)

Status flags (to avoid reprocessing)
- Uses a new flag to avoid interference with previous runs:
  - status.myj_movie_sync2: 'matched' | 'not_found'
  - status.myj_movie_sync2_at: UTC timestamp

CLI
  python script/db/merge_myj_movies.py \
    --mongo "mongodb://user:pass@host:27017/admin" \
    --jdb jdb --myj myj --limit 0 --resume
"""

import argparse
import datetime as dt
import os
from typing import Any, Dict, List, Optional, Tuple

from pymongo import MongoClient
from tqdm import tqdm


def _canon(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    s = str(code).strip().upper()
    # Drop all non-alnum
    s = "".join(ch for ch in s if ch.isalnum())
    return s or None


def _split_letters_digits(code: str) -> Tuple[str, str]:
    """Split canonical code into (letters, digits+suffix)."""
    letters = []
    rest = []
    hit_digit = False
    for ch in code:
        if not hit_digit and ch.isalpha():
            letters.append(ch)
        else:
            hit_digit = True
            rest.append(ch)
    return ("".join(letters), "".join(rest))


def build_myj_index(
    myj_col,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    idx: Dict[str, Dict[str, Any]] = {}
    tail: Dict[str, Dict[str, Any]] = {}
    for m in myj_col.find(
        {},
        projection={
            "code": 1,
            "screenshots": 1,
            "profile": 1,
            "link": 1,
            "description": 1,
            "publisher": 1,
        },
    ):
        key = _canon(m.get("code"))
        if not key:
            continue
        idx[key] = m
        letters, digits = _split_letters_digits(key)
        if digits:
            tail_letters = letters[-4:] if letters else ""
            tkey = f"{tail_letters}{digits}"
            tail[tkey] = m
    return idx, tail


def main():
    parser = argparse.ArgumentParser(
        description="Merge myj.movies into jdb.movies by code"
    )
    parser.add_argument(
        "--mongo",
        default=os.getenv(
            "MONGO_URL", "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
        ),
    )
    parser.add_argument("--jdb", default=os.getenv("MONGO_DB_NAME", "jdb"))
    parser.add_argument("--myj", default=os.getenv("MYJ_DB_NAME", "myj"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")

    args = parser.parse_args()

    client = MongoClient(args.mongo)
    jdb = client[args.jdb]
    myj = client[args.myj]

    col_jdb = jdb["movies"]
    # Source collection in myj DB is named 'movie' (singular)
    col_myj = myj["movie"]

    idx, tail_idx = build_myj_index(col_myj)

    # Remove old flag from previous runs
    try:
        jdb["movies"].update_many({}, {"$unset": {"status.myj_movie_sync": ""}})
    except Exception:
        pass

    # Target query: skip docs where code is null; optionally skip already processed
    base_q: Dict[str, Any] = {"code": {"$ne": None}}
    q: Dict[str, Any] = dict(base_q)
    if args.resume:
        resume_clause = {
            "$or": [
                {"status.myj_movie_sync2": {"$exists": False}},
                {"status.myj_movie_sync2": {"$nin": ["matched", "not_found"]}},
            ]
        }
        q = {"$and": [base_q, resume_clause]}

    total = col_jdb.count_documents(q)
    if args.limit and args.limit < total:
        total = args.limit

    pbar = tqdm(total=total, desc="合并myj电影", unit="movie", ncols=120)

    processed = 0
    matched = 0
    updated = 0
    not_found = 0
    cursor = col_jdb.find(
        q, projection={"_id": 1, "href": 1, "code": 1, "title": 1, "publisher": 1}
    )
    for mv in cursor:
        if args.limit and processed >= args.limit:
            break
        href = mv.get("href")
        title = mv.get("title") or ""
        pbar.set_postfix_str(f"{href} {title}")

        ckey = _canon(mv.get("code"))
        src = idx.get(ckey) if ckey else None
        if not src and ckey:
            letters, digits = _split_letters_digits(ckey)
            if digits:
                tkey = f"{letters[-4:]}{digits}"
                src = tail_idx.get(tkey)

        status_patch: Dict[str, Any] = {
            "status.myj_movie_sync2_at": dt.datetime.now(dt.timezone.utc)
        }

        if src:
            update: Dict[str, Any] = {}

            # direct overwrite fields
            if "screenshots" in src:
                update["screenshots2"] = src.get("screenshots")
            if "profile" in src:
                update["profile"] = src.get("profile")
            if "link" in src:
                update["link"] = src.get("link")
            if "description" in src:
                update["description"] = src.get("description")

            # publisher: only when missing/null/empty
            if src.get("publisher") is not None:
                pub_cur = mv.get("publisher")
                if pub_cur in (None, "", {}):
                    update["publisher"] = src.get("publisher")

            status_patch["status.myj_movie_sync2"] = "matched"
            matched += 1
            if update:
                col_jdb.update_one(
                    {"_id": mv["_id"]}, {"$set": {**update, **status_patch}}
                )
                updated += 1
            else:
                col_jdb.update_one({"_id": mv["_id"]}, {"$set": status_patch})
        else:
            status_patch["status.myj_movie_sync2"] = "not_found"
            col_jdb.update_one({"_id": mv["_id"]}, {"$set": status_patch})
            not_found += 1

        processed += 1
        pbar.update(1)

    pbar.close()
    print(
        f"完成：处理 {processed} 部影片；匹配 {matched}，更新 {updated}，未匹配 {not_found}；"
        f"myj 索引 {len(idx)} 条，尾索引 {len(tail_idx)} 条"
    )


if __name__ == "__main__":
    main()
