from __future__ import annotations

"""
Merge actress data from `myj.actress` into `jdb.actors`.

Rules
- Only process `jdb.actors` where `category == 'censored'`.
- Match by name: split `jdb.actor.title` by common separators and look for any
  token that exactly equals `myj.actress.japan_name`.
- Update keys on jdb actor: `profile`, `japan_name`, `roman_name`, `publisher`,
  `link`, and `official_movies` (from myj.movies).
- Maintain a status flag to avoid duplicate work: `status.myj_sync` in
  {'matched', 'not_found'} and `status.myj_sync_at` timestamp.
- When merging:
  - For dict `profile`: merge keys, do not overwrite existing non-empty values.
  - For list `official_movies`: merge by unique 'link' (or 'id' fallback).
  - For scalars (japan_name/roman_name/publisher/link): only set when missing.

CLI
  python script/db/merge_myj_actors.py \
    --mongo "mongodb://user:pass@host:27017/admin" \
    --jdb jdb --myj myj \
    --batch 200 --limit 0 --resume
"""

import argparse
import datetime as dt
import os
from typing import Any, Dict, Iterable, List, Optional

from pymongo import MongoClient
from tqdm import tqdm


def _names_from_title(title: Optional[str]) -> List[str]:
    if not title:
        return []
    seps = [",", "，", "、", "/", "|", " "]
    s = title
    for sep in seps:
        s = s.replace(sep, "|")
    parts = [p.strip() for p in s.split("|") if p.strip()]
    # 去重，保持顺序
    seen = set()
    out: List[str] = []
    for p in parts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def _merge_profile(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(dst, dict):
        dst = {}
    if not isinstance(src, dict):
        return dst
    merged = dict(dst)
    for k, v in src.items():
        if k not in merged or merged[k] in (None, ""):
            merged[k] = v
    return merged


def _merge_official_movies(
    dst: List[Dict[str, Any]], src: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    dst = list(dst or [])
    seen = set()
    for it in dst:
        key = it.get("link") or it.get("id")
        if key:
            seen.add(key)
    for it in src or []:
        key = it.get("link") or it.get("id")
        if key and key not in seen:
            dst.append(it)
            seen.add(key)
    return dst


def main():
    parser = argparse.ArgumentParser(description="Merge myj.actress into jdb.actors")
    parser.add_argument(
        "--mongo",
        default=os.getenv(
            "MONGO_URL", "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
        ),
    )
    parser.add_argument(
        "--jdb", default=os.getenv("MONGO_DB_NAME", "jdb"), help="target DB name"
    )
    parser.add_argument(
        "--myj", default=os.getenv("MYJ_DB_NAME", "myj"), help="source DB name"
    )
    parser.add_argument("--batch", type=int, default=200)
    parser.add_argument(
        "--limit", type=int, default=0, help="limit actors processed (0=no limit)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="skip docs already marked matched/not_found",
    )
    parser.add_argument(
        "--category",
        choices=["censored", "uncensored", "all"],
        default="censored",
        help="which actor category to process",
    )

    args = parser.parse_args()

    client = MongoClient(args.mongo)
    jdb = client[args.jdb]
    myj = client[args.myj]

    jdb_actors = jdb["actors"]
    myj_actress = myj["actress"]

    # 构建 japan_name -> myj 文档的索引
    name_map: Dict[str, Dict[str, Any]] = {}
    for a in myj_actress.find(
        {},
        projection={
            "japan_name": 1,
            "profile": 1,
            "roman_name": 1,
            "publisher": 1,
            "link": 1,
            "movies": 1,
            "avatar": 1,
        },
    ):
        name = a.get("japan_name")
        if not name:
            continue
        name_map[str(name)] = a

    # 处理类别：censored/uncensored/all；支持 resume
    if args.category == "all":
        q: Dict[str, Any] = {"category": {"$in": ["censored", "uncensored"]}}
    else:
        q = {"category": args.category}
    if args.resume:
        q["$or"] = [
            {"status.myj_sync": {"$exists": False}},
            {"status.myj_sync": {"$nin": ["matched", "not_found"]}},
        ]

    total = jdb_actors.count_documents(q)
    if args.limit and args.limit < total:
        total = args.limit

    pbar = tqdm(
        total=total, desc=f"合并myj演员[{args.category}]", unit="actor", ncols=120
    )

    cursor = jdb_actors.find(
        q,
        projection={
            "href": 1,
            "name": 1,
            "title": 1,
            "status": 1,
            "official_movies": 1,
            "profile": 1,
            "japan_name": 1,
            "roman_name": 1,
            "publisher": 1,
            "link": 1,
            "avatar2": 1,
        },
    )
    processed = 0

    for actor in cursor:
        if args.limit and processed >= args.limit:
            break
        href = actor.get("href")
        name = actor.get("name") or actor.get("title") or ""
        pbar.set_postfix_str(f"{href} {name}")

        titles = _names_from_title(actor.get("title"))
        matched_doc = None
        matched_name = None
        for t in titles:
            if t in name_map:
                matched_doc = name_map[t]
                matched_name = t
                break

        status_patch: Dict[str, Any] = {
            "status.myj_sync_at": dt.datetime.now(dt.timezone.utc)
        }

        if matched_doc:
            # 构建更新内容
            update: Dict[str, Any] = {}

            # profile merge
            update["profile"] = _merge_profile(
                actor.get("profile") or {}, matched_doc.get("profile") or {}
            )

            # avatar from myj -> avatar2 (add if missing)
            if matched_doc.get("avatar") and not actor.get("avatar2"):
                update["avatar2"] = matched_doc.get("avatar")

            # japan_name: write into top-level field (no longer inside status)
            candidate_jn = matched_name or matched_doc.get("japan_name")
            if candidate_jn and not actor.get("japan_name"):
                update["japan_name"] = candidate_jn

            # roman_name / publisher: fill when missing
            for key in ("roman_name", "publisher"):
                if not actor.get(key) and matched_doc.get(key):
                    update[key] = matched_doc.get(key)

            # link: ensure set to official link from myj
            if matched_doc.get("link"):
                update["link"] = matched_doc.get("link")

            # official_movies merge
            update["official_movies"] = _merge_official_movies(
                actor.get("official_movies") or [], matched_doc.get("movies") or []
            )

            status_patch["status.myj_sync"] = "matched"

            # 执行更新
            jdb_actors.update_one(
                {"_id": actor["_id"]}, {"$set": {**update, **status_patch}}
            )
        else:
            status_patch["status.myj_sync"] = "not_found"
            jdb_actors.update_one({"_id": actor["_id"]}, {"$set": status_patch})

        processed += 1
        pbar.update(1)

    pbar.close()
    print(f"完成：处理 {processed} 位演员，来源文档 {len(name_map)}")


if __name__ == "__main__":
    main()
