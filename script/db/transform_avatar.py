from __future__ import annotations

"""
Transform downloaded actor avatars from hash-sharded layout to href-based layout.

For each document in the given collection (default: actors):
  - Read `href` (e.g., '/actors/MkAX') and `avatar` current path.
  - Find the current image file (avatar path is expected to be a relative path like 'img/avatar/ab/12/<hash>.jpg').
  - Move/rename it to `<dest_root>/<href>.jpg`, i.e., keep directory structure matching href and filename the last segment + '.jpg'.
  - Update the document's `avatar` to 'local' (or boolean true with --bool) to indicate locally available.

Usage:
  python script/db/transform_avatar.py \
    --collection actors \
    --href-field href \
    --avatar-field avatar \
    --dest-root img/avatar
"""

import argparse
import os
import shutil
from typing import Any, Dict

from pymongo import MongoClient

try:
    from base import mongo_url, db_name  # type: ignore
except Exception:
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGO_DB_NAME", "test")


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform avatar paths to href-based layout and mark local"
    )
    parser.add_argument("--collection", default="actors")
    parser.add_argument("--href-field", default="href")
    parser.add_argument("--avatar-field", default="avatar")
    parser.add_argument(
        "--dest-root", required=True, help="base folder for avatars, e.g., img/avatar"
    )
    parser.add_argument(
        "--query",
        default="{}",
        help="additional match JSON, default selects avatar not 'local'",
    )
    parser.add_argument(
        "--bool",
        dest="mark_bool",
        action="store_true",
        help="mark avatar as boolean true instead of 'local'",
    )
    args = parser.parse_args()

    import json

    try:
        extra_match = json.loads(args.query)
    except Exception:
        raise SystemExit("--query must be valid JSON string")

    client = MongoClient(mongo_url)
    db = client[db_name]
    col = db[args.collection]

    # default match: avatar exists and is not 'local'/True
    match: Dict[str, Any] = {
        args.href_field: {"$exists": True},
        args.avatar_field: {"$exists": True, "$nin": ["local", True]},
    }
    if extra_match:
        match.update(extra_match)

    cur = col.find(match, projection={args.href_field: 1, args.avatar_field: 1})

    try:
        from tqdm import tqdm  # type: ignore

        total = col.count_documents(match)
        pbar = tqdm(total=total, desc="转换头像", unit="doc", ncols=100)
    except Exception:
        pbar = None

    moved = updated = skipped = 0
    for doc in cur:
        href = str(doc.get(args.href_field) or "").lstrip("/")
        avatar_path = str(doc.get(args.avatar_field) or "").replace("\\", "/")
        if not href or not avatar_path:
            skipped += 1
            if pbar:
                pbar.update(1)
            continue
        # current file may be relative (recommended). If absolute, use directly.
        src = avatar_path
        if not os.path.isabs(src):
            # treat as relative to CWD
            src = os.path.join(src)
        # destination: <dest_root>/<href>.jpg
        last_segment = os.path.basename(href)  # e.g., MkAX
        dest_dir = os.path.join(args.dest_root, os.path.dirname(href))
        ensure_parent(os.path.join(args.dest_root, href + ".jpg"))
        dest = os.path.join(args.dest_root, href + ".jpg")

        try:
            if os.path.exists(src):
                if not os.path.exists(dest):
                    shutil.move(src, dest)
                moved += 1
            else:
                skipped += 1
            # mark avatar as local
            new_val = True if args.mark_bool else "local"
            col.update_one({"_id": doc["_id"]}, {"$set": {args.avatar_field: new_val}})
            updated += 1
        except Exception:
            skipped += 1
        finally:
            if pbar:
                pbar.update(1)

    if pbar:
        pbar.close()

    print({"moved": moved, "updated": updated, "skipped": skipped})


if __name__ == "__main__":
    main()
