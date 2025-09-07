from __future__ import annotations

"""
Batch image downloader for MongoDB documents.

Features
- Query a collection for documents (e.g., actors) with image URLs in a field (e.g., 'avatar').
- Download in small batches with a single requests.Session per batch (default 50 docs/batch).
- Naming modes:
  - hash: save as img_root/ab/12/<md5>.jpg (default)
  - by_href: save as img_root/<doc.href>/<basename(url)>
  - by_url_path: save as img_root/<url.path> and store '/<url.path>' to DB
- Update the document's field to the relative path (e.g., 'img/avatar/ab/12/<hash>.jpg').
- Generic for single-value string field or list field (e.g., screenshots).

CLI
  python script/db/picture.py \
    --collection actors \
    --field avatar \
    --root img/avatar \
    --query '{"avatar": {"$regex": "^http"}}' \
    --batch 50
"""

import argparse
import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple
from tqdm import tqdm
import requests
from pymongo import MongoClient

# Reuse connection defaults if available
try:
    from base import mongo_url, db_name  # type: ignore
except Exception:
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGO_DB_NAME", "test")


def _md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _save_image_bytes(root: str, data: bytes) -> str:
    """Save image bytes under root using hash-based sharding.

    Layout: root/ab/12/<hash>.jpg
    Returns relative path with forward slashes.
    """
    h = _md5_hex(data)
    a, b = h[:2], h[2:4]
    dir_path = os.path.join(root, a, b)
    os.makedirs(dir_path, exist_ok=True)
    fp = os.path.join(dir_path, f"{h}.jpg")
    if not os.path.exists(fp):
        with open(fp, "wb") as f:
            f.write(data)
    rel = fp.replace("\\", "/")
    return rel


def _save_image_by_href(root: str, href_path: str, url: str, data: bytes) -> str:
    """Save image under root/<href_path>/<filename-from-url>.

    href_path: like '/v/abcd' or 'actors/MkAX' (leading slash allowed).
    url: original image URL, the basename (last segment) will be used.
    Returns relative path.
    """
    # sanitize
    href_path = (href_path or "").lstrip("/")
    filename = os.path.basename(url.split("?")[0]) or "image.jpg"
    # ensure extension
    if "." not in filename:
        filename = filename + ".jpg"
    dir_path = os.path.join(root, href_path)
    os.makedirs(dir_path, exist_ok=True)
    fp = os.path.join(dir_path, filename)
    if not os.path.exists(fp):
        with open(fp, "wb") as f:
            f.write(data)
    return fp.replace("\\", "/")


def _save_image_by_url_path(root: str, url: str, session: Optional[requests.Session] = None, timeout: int = 15) -> Optional[str]:
    """Save image under root + url path, and return DB relative path starting with '/'.

    Example: url=https://c0.jdbstatic.com/thumbs/gz/GZdV1q.jpg
             saved to <root>/thumbs/gz/GZdV1q.jpg
             returns '/thumbs/gz/GZdV1q.jpg'
    """
    from urllib.parse import urlparse

    try:
        p = urlparse(url)
        if not p.path:
            return None
        rel_path = p.path  # startswith '/'
        full_path = os.path.join(root, rel_path.lstrip('/'))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not os.path.exists(full_path):
            sess = session or requests.Session()
            r = sess.get(url, timeout=timeout)
            if not r.ok:
                return None
            with open(full_path, 'wb') as f:
                f.write(r.content)
        return rel_path
    except Exception:
        return None


def _iter_docs(col, query: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    # Use a server-side cursor; let caller slice into batches
    return col.find(query, projection={})


def _extract_urls(doc: Dict[str, Any], field: str) -> Tuple[List[str], bool]:
    """Return (urls, is_list_field). Only http(s) URLs are returned."""
    v = doc.get(field)
    if v is None:
        return [], False
    if isinstance(v, list):
        urls = [x for x in v if isinstance(x, str) and x.startswith("http")]
        return urls, True
    if isinstance(v, str) and v.startswith("http"):
        return [v], False
    return [], False


def download_images_for_field(
    *,
    mongo_uri: str,
    db_name: str,
    collection: str,
    find_query: Dict[str, Any],
    field: str,
    target_root: str,
    batch_size: int = 50,
    timeout: int = 15,
    naming: str = "hash",  # 'hash' | 'by_href' | 'by_url_path'
    href_field: str = "href",
    mark_local: bool = False,
) -> Dict[str, int]:
    """
    Download images for the given field and update documents with relative paths.

    - For string field: set the field to the relative path string.
    - For list field: replace each URL with its relative path (non-URL entries are preserved).
    """
    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db[collection]

    processed = 0
    updated = 0
    downloaded = 0
    errors = 0

    # progress bar (tqdm) with remaining count and ETA
    total_docs = col.count_documents(find_query)

    pbar = tqdm(total=total_docs, desc="下载图片", unit="doc", ncols=100)

    cursor = _iter_docs(col, find_query)

    batch: List[Dict[str, Any]] = []
    for doc in cursor:
        batch.append(doc)
        if len(batch) >= batch_size:
            _do_batch(
                batch,
                col,
                field,
                target_root,
                timeout,
                naming,
                href_field,
                mark_local,
                stats=(
                    lambda u, d, e: (
                        globals().__setitem__("__u", u),
                        globals().__setitem__("__d", d),
                        globals().__setitem__("__e", e),
                    )
                ),
            )
            # stats accumulation via returns
            u, d, e = __u, __d, __e  # type: ignore # pulled from lambda side-effects
            updated += u
            downloaded += d
            errors += e
            processed += len(batch)
            if pbar:
                pbar.update(len(batch))
                remaining = (pbar.total - pbar.n) if pbar.total is not None else 0
                pbar.set_postfix_str(f"剩余:{remaining}")
            batch = []

    if batch:
        _do_batch(
            batch,
            col,
            field,
            target_root,
            timeout,
            naming,
            href_field,
            mark_local,
            stats=(
                lambda u, d, e: (
                    globals().__setitem__("__u", u),
                    globals().__setitem__("__d", d),
                    globals().__setitem__("__e", e),
                )
            ),
        )
        u, d, e = __u, __d, __e  # type: ignore
        updated += u
        downloaded += d
        errors += e
        processed += len(batch)
        if pbar:
            pbar.update(len(batch))
            remaining = (pbar.total - pbar.n) if pbar.total is not None else 0
            pbar.set_postfix_str(f"剩余:{remaining}")

    if pbar:
        pbar.close()

    return {
        "processed": processed,
        "updated": updated,
        "downloaded": downloaded,
        "errors": errors,
    }


def _do_batch(
    docs: List[Dict[str, Any]],
    col,
    field: str,
    target_root: str,
    timeout: int,
    naming: str,
    href_field: str,
    mark_local: bool,
    stats,
) -> None:
    session = requests.Session()
    u = d = e = 0
    for doc in docs:
        urls, is_list = _extract_urls(doc, field)
        if not urls:
            continue
        try:
            if not is_list:
                url = urls[0]
                r = session.get(url, timeout=timeout)
                if not r.ok:
                    e += 1
                    continue
                if naming == "by_href":
                    href_path = str(doc.get(href_field, ""))
                    rel = _save_image_by_href(target_root, href_path, url, r.content)
                elif naming == "by_url_path":
                    saved = _save_image_by_url_path(target_root, url, session=session, timeout=timeout)
                    if not saved:
                        e += 1
                        continue
                    rel = saved
                else:
                    rel = _save_image_bytes(target_root, r.content)
                new_val: Any = ("local" if mark_local else rel)
                col.update_one({"_id": doc["_id"]}, {"$set": {field: new_val}})
                u += 1
                d += 1
            else:
                new_list: List[str] = []
                for item in doc.get(field) or []:
                    if isinstance(item, str) and item.startswith("http"):
                        try:
                            r = session.get(item, timeout=timeout)
                            if not r.ok:
                                e += 1
                                new_list.append(item)
                                continue
                            if naming == "by_href":
                                href_path = str(doc.get(href_field, ""))
                                relp = _save_image_by_href(target_root, href_path, item, r.content)
                            elif naming == "by_url_path":
                                saved = _save_image_by_url_path(target_root, item, session=session, timeout=timeout)
                                relp = saved or item
                            else:
                                relp = _save_image_bytes(target_root, r.content)
                            d += 1
                            new_list.append(relp)
                        except requests.RequestException:
                            e += 1
                            new_list.append(item)
                    else:
                        new_list.append(item)
                col.update_one({"_id": doc["_id"]}, {"$set": {field: new_list}})
                u += 1
        except requests.RequestException:
            e += 1
            continue
    stats(u, d, e)


def main():
    parser = argparse.ArgumentParser(
        description="Batch download images and update MongoDB paths"
    )
    parser.add_argument("--collection", required=True)
    parser.add_argument("--field", required=True)
    parser.add_argument(
        "--root", required=True, help="target root folder, e.g., img/avatar"
    )
    parser.add_argument("--query", default="{}", help="Mongo find query as JSON string")
    parser.add_argument("--batch", type=int, default=50)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--mongo", default=mongo_url)
    parser.add_argument("--db", default=db_name)
    parser.add_argument("--naming", choices=["hash", "by_href", "by_url_path"], default="hash",
                        help="hash: shard by md5; by_href: save under <root>/<href>/<basename(url)>; by_url_path: save under <root>/<url.path>")
    parser.add_argument("--href-field", default="href",
                        help="document field that stores href path when naming=by_href")
    parser.add_argument("--mark-local", action="store_true",
                        help="set field to 'local' instead of relative path (only for string field)")
    args = parser.parse_args()

    try:
        find_query = json.loads(args.query)
    except Exception:
        raise SystemExit("--query must be a valid JSON string")

    os.makedirs(args.root, exist_ok=True)
    stats = download_images_for_field(
        mongo_uri=args.mongo,
        db_name=args.db,
        collection=args.collection,
        find_query=find_query,
        field=args.field,
        target_root=args.root,
        batch_size=args.batch,
        timeout=args.timeout,
        naming=args.naming,
        href_field=args.href_field,
        mark_local=args.mark_local,
    )
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()

    # 下载avatar: python db/picture.py --collection actors --field avatar --root /Volumes/images/jdb/avatar --query '{"avatar":{"$regex":"^http"}}' --batch 50
