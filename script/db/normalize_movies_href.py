from __future__ import annotations

"""
Normalize movies.href to be relative path (remove base_url) and merge duplicates.

Usage:
  python script/tools/normalize_movies_href.py

Behavior:
  - For every document in `movies` where `href` starts with http/https,
    compute its path via urlparse and normalize to that relative path.
  - If a document already exists with the same relative path, merge fields
    (lists are de-duplicated, dicts merged by non-empty preference), then
    delete the absolute-href document. Otherwise, update href in-place.
"""

import re
from typing import Any, Dict, List
from urllib.parse import urlparse
from datetime import datetime, timezone

from pymongo import MongoClient

# Reuse the same connection defaults as other scripts
from base import mongo_url, db_name  # type: ignore


def merge_values(a, b):
    return b if (a is None or a == "" or a == []) else a


def merge_lists(a_list, b_list):
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


def merge_docs(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(target)
    for k, v in source.items():
        if k == "_id":
            continue
        tv = merged.get(k)
        if isinstance(tv, list) or isinstance(v, list):
            merged[k] = merge_lists(
                tv if isinstance(tv, list) else [], v if isinstance(v, list) else []
            )
        elif isinstance(tv, dict) and isinstance(v, dict):
            mv = dict(tv)
            for kk, vv in v.items():
                if kk == "_id":
                    continue
                mv[kk] = merge_values(mv.get(kk), vv)
            merged[k] = mv
        else:
            merged[k] = merge_values(tv, v)
    return merged


def to_path(href: str) -> str | None:
    try:
        p = urlparse(href)
        if p.scheme and p.netloc and p.path:
            return p.path
    except Exception:
        return None
    return None


def main() -> None:
    client = MongoClient(mongo_url)
    db = client[db_name]
    col = db["actors"]

    abs_cur = col.find({"href": {"$regex": r"^https?://"}}, {"href": 1})
    total = col.count_documents({"href": {"$regex": r"^https?://"}})
    processed = 0
    merged_cnt = 0
    updated_cnt = 0

    print(f"[normalize] total absolute href docs: {total}")
    for doc in abs_cur:
        processed += 1
        href = doc.get("href")
        if not isinstance(href, str):
            continue
        path = to_path(href)
        if not path:
            continue

        rel = col.find_one({"href": path})
        if rel and rel["_id"] != doc["_id"]:
            # merge into rel, delete current abs
            full_abs = col.find_one({"_id": doc["_id"]}) or {}
            merged = merge_docs(rel, full_abs)
            merged.setdefault("href", path)
            col.update_one({"_id": rel["_id"]}, {"$set": merged})
            col.delete_one({"_id": doc["_id"]})
            merged_cnt += 1
        else:
            # simply update href to path
            col.update_one({"_id": doc["_id"]}, {"$set": {"href": path}})
            updated_cnt += 1

        if processed % 100 == 0:
            print(
                f"[normalize] processed {processed}/{total} (merged={merged_cnt}, updated={updated_cnt})"
            )

    print(
        f"[normalize] done. processed={processed}, merged={merged_cnt}, updated={updated_cnt}"
    )


if __name__ == "__main__":
    main()
