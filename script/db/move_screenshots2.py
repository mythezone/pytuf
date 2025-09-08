from __future__ import annotations

"""
Move/rehydrate `screenshots2` files for jdb.movies.

Input format per item: "<md5hash>:<filename>" (e.g.,
"4a5cc8316f581586f3f7d2530207f6c2:ONSD340_0.jpg"). The source file is
expected at: <src_root>/<h0h1>/<h2h3>/<filename> (i.e., use the part after the
colon as the basename; directory sharding uses the hash prefixes only).

Destination layout is derived from movie href '/v/<RID>':
  <dst_root>/<RID[:2]>/<RID>/<filename>

The script copies files to destination and rewrites `screenshots2` items to the
new relative path using forward slashes. Non-conforming items (e.g., starting
with 'http') are kept as-is and counted.

A status flag is added on the movie doc to avoid reprocessing:
  status.screenshots2_moved = true
  status.screenshots2_moved_at = <UTC datetime>
"""

import argparse
import datetime as dt
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pymongo import MongoClient
from tqdm import tqdm


PAIR_RE = re.compile(r"^([0-9a-fA-F]{32}):(.+)$")


def src_candidate_paths(src_root: str, h: str, filename: str) -> List[Path]:
    """Return candidate source paths for a given hash and filename.

    Correct layout: <src_root>/<h0h1>/<h2h3>/<filename>
    """
    base = Path(src_root) / h[:2] / h[2:4]
    return [base / filename]


def build_store_and_fs_paths(href: str, filename: str) -> Tuple[str, Path]:
    """Return (store_path, fs_rel_path) for a given movie href + filename.

    - store_path: path to be saved into Mongo, starts with '/samples/...'
    - fs_rel_path: path used under dst_root directory (no leading slash, and
      without the 'samples' segment): '<rid[:2].lower()>/<filename>'
    """
    rid = (href or "").strip("/").split("/")[-1]
    prefix = rid[:2].lower() if rid else ""
    store_path = f"/samples/{prefix}/{filename}" if prefix else f"/samples/{filename}"
    fs_rel = Path(prefix) / filename if prefix else Path(filename)
    return store_path, fs_rel


def process_movies(
    *,
    mongo_uri: str,
    db_name: str,
    collection: str,
    src_root: str,
    dst_root: str,
    limit: int = 0,
    resume: bool = True,
) -> Dict[str, int]:
    client = MongoClient(mongo_uri)
    col = client[db_name][collection]

    base_q: Dict[str, Any] = {
        "screenshots2": {"$exists": True, "$type": "array", "$ne": []}
    }
    q: Dict[str, Any] = dict(base_q)
    if resume:
        q = {
            "$and": [
                base_q,
                {
                    "$or": [
                        {"status.screenshots2_moved": {"$exists": False}},
                        {"status.screenshots2_moved": {"$ne": True}},
                    ]
                },
            ]
        }

    total = col.count_documents(q)
    if limit and limit < total:
        total = limit

    pbar = tqdm(total=total, desc="迁移screenshots2", unit="movie", ncols=120)

    processed = 0
    updated_docs = 0
    incompatible = 0
    copied_files = 0
    missing_files = 0

    cursor = col.find(q, projection={"_id": 1, "href": 1, "screenshots2": 1})
    for doc in cursor:
        if limit and processed >= limit:
            break

        href = doc.get("href") or ""
        items = list(doc.get("screenshots2") or [])
        new_items: List[str] = []
        changed = False

        for item in items:
            if isinstance(item, str):
                m = PAIR_RE.match(item)
                if m:
                    h, filename = m.group(1), m.group(2)
                    # locate source
                    src_path: Path | None = None
                    for cand in src_candidate_paths(src_root, h, filename):
                        try:
                            if cand.exists():
                                src_path = cand
                                break
                        except OSError:
                            # I/O error when stat-ing a path on network drive; treat as missing
                            continue
                    if not src_path:
                        # source missing: mark with flag and count
                        new_items.append(f"{item}-not-exist")
                        missing_files += 1
                        changed = True
                        continue

                    store_path, fs_rel = build_store_and_fs_paths(href, filename)
                    full_dst = Path(dst_root) / fs_rel
                    full_dst.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        if not full_dst.exists():
                            shutil.copy2(src_path, full_dst)
                            copied_files += 1
                        # store path begins with '/samples/...'
                        new_items.append(store_path)
                        changed = True
                    except Exception:
                        # copy error: mark as not-exist as well
                        new_items.append(f"{item}-not-exist")
                        missing_files += 1
                        changed = True
                else:
                    # keep urls or other formats unchanged
                    if item.startswith("http"):
                        new_items.append(item)
                    else:
                        incompatible += 1
                        new_items.append(item)
            else:
                incompatible += 1
                new_items.append(item)

        if changed:
            col.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "screenshots2": new_items,
                        "status.screenshots2_moved": True,
                        "status.screenshots2_moved_at": dt.datetime.now(
                            dt.timezone.utc
                        ),
                    }
                },
            )
            updated_docs += 1
        else:
            col.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "status.screenshots2_moved": True,
                        "status.screenshots2_moved_at": dt.datetime.now(
                            dt.timezone.utc
                        ),
                    }
                },
            )

        processed += 1
        pbar.set_postfix_str(f"{href}")
        pbar.update(1)

    pbar.close()
    return {
        "processed": processed,
        "updated_docs": updated_docs,
        "copied_files": copied_files,
        "incompatible_items": incompatible,
        "missing_files": missing_files,
    }


def main():
    ap = argparse.ArgumentParser(description="Copy and rewrite screenshots2 paths")
    ap.add_argument(
        "--mongo",
        default=os.getenv(
            "MONGO_URL", "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
        ),
    )
    ap.add_argument("--db", default=os.getenv("MONGO_DB_NAME", "jdb"))
    ap.add_argument("--collection", default="movies")
    ap.add_argument("--src-root", required=True, help="source hash-sharded root folder")
    ap.add_argument(
        "--dst-root", required=True, help="destination root folder for jdb screenshots"
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-resume", dest="resume", action="store_false")
    ap.set_defaults(resume=True)
    args = ap.parse_args()

    stats = process_movies(
        mongo_uri=args.mongo,
        db_name=args.db,
        collection=args.collection,
        src_root=args.src_root,
        dst_root=args.dst_root,
        limit=args.limit,
        resume=args.resume,
    )
    print(stats)


if __name__ == "__main__":
    main()
