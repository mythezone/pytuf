from __future__ import annotations

"""
Scan given root folders for large video files and export a CSV mapping
  root, relative_path, code, href

Rules
- Only files larger than a threshold (default 1 GiB)
- Video extensions: mp4,mkv,avi,wmv,mov,iso,ts,m2ts,flv,mpg,mpeg,webm
- Code detection: search filename (without extension) for pattern like
  '<LETTERS>-?<DIGITS>[LETTER?]' (e.g., 'AARM-192', 'abw149', 'IPX123')
  The output code will be canonicalized to 'LETTERS-DIGITS[suffix]' in upper
  case (e.g., 'AARM-192', 'ABW-149', 'IPX-123').
- DB lookup: query jdb.movies by code case-insensitively with optional hyphen
  (letters + optional '-' + digits + optional letter suffix). If found, write
  href into CSV; otherwise leave empty.

Usage
  python script/db/scan_videos_to_csv.py \
    --roots /path/to/drive1 /path/to/drive2 \
    --out /tmp/videos.csv \
    --mongo "mongodb://..." --db jdb
"""

import argparse
import csv
import os
import re
import platform
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from pymongo import MongoClient
from tqdm import tqdm

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore

# Defaults from script/base.py if available
try:
    from script.base import mongo_url as DEFAULT_MONGO_URL  # type: ignore
    from script.base import db_name as DEFAULT_DB_NAME  # type: ignore
except Exception:
    DEFAULT_MONGO_URL = os.getenv(
        "MONGO_URL", "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
    )
    DEFAULT_DB_NAME = os.getenv("MONGO_DB_NAME", "jdb")


VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".wmv", ".mov", ".iso", ".ts", ".m2ts", ".flv", ".mpg", ".mpeg", ".webm"}
SIZE_MIN = 1 * 1024 * 1024 * 1024  # 1 GiB

CODE_RE = re.compile(r"([A-Za-z]{2,8})[-_ ]?(\d{2,6}[A-Za-z]?)")

# directories to skip (system/recycle/noisy)
SKIP_DIR_NAMES = {
    "$RECYCLE.BIN",
    "RECYCLE",
    "RECYCLER",
    "@Recycle",
    "System Volume Information",
    "lost+found",
    "__MACOSX",
    ".Trashes",
    ".Trash",
    ".DS_Store",
    ".Spotlight-V100",
    ".TemporaryItems",
    ".fseventsd",
    "@eaDir",
    "node_modules",
    ".git",
}


def _walk_candidates(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for fn in filenames:
            p = Path(dirpath) / fn
            ext = p.suffix.lower()
            if ext not in VIDEO_EXTS:
                continue
            try:
                sz = p.stat().st_size
            except OSError:
                continue
            if sz < SIZE_MIN:
                continue
            yield p


def count_candidates(root: Path) -> int:
    return sum(1 for _ in _walk_candidates(root))


def detect_code_from_filename(path: Path) -> Optional[str]:
    name = path.stem  # without extension
    m = CODE_RE.search(name)
    if not m:
        return None
    letters = m.group(1).upper()
    digits = m.group(2).upper()
    return f"{letters}-{digits}"


def mongo_find_href_by_code(
    client: MongoClient, db_name: str, code: str
) -> Optional[str]:
    letters, digits = _split_letters_digits(_canon(code) or "")
    if not letters or not digits:
        return None
    pattern = f"^{re.escape(letters)}[- ]?{re.escape(digits)}$"
    col = client[db_name]["movies"]
    doc = col.find_one(
        {"code": {"$regex": pattern, "$options": "i"}}, projection={"href": 1}
    )
    return doc.get("href") if doc else None


def _canon(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    s = str(code).strip().upper()
    s = "".join(ch for ch in s if ch.isalnum())
    return s or None


def _split_letters_digits(code: str) -> Tuple[str, str]:
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


def main():
    ap = argparse.ArgumentParser(
        description="Scan videos and export CSV with code/href matches"
    )
    # OS-specific default roots
    default_mac_roots = [
        "/Volumes/disk/D/Adult",
        "/Volumes/disk/G/Adult",
        "/Volumes/disk/J/Adult",
        "/Volumes/disk/media/16t/Adult",
    ]
    default_sta_roots = [
        "/disk/D/Adult",
        "/disk/G/Adult",
        "/disk/J/Adult",
        "/disk/media/16t/Adult",
    ]

    def _pick_roots() -> list[str]:
        sysname = platform.system()
        if sysname == "Darwin":
            return default_mac_roots
        if sysname == "Linux":
            # Try detect Ubuntu specifically
            try:
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    data = f.read().lower()
                if "ubuntu" in data:
                    return default_sta_roots
            except Exception:
                pass
            return default_sta_roots
        # fallback
        return default_mac_roots

    ap.add_argument(
        "--roots",
        nargs="+",
        default=_pick_roots(),
        help="one or more root folders to scan",
    )
    ap.add_argument("--out", required=True, help="output CSV file path")
    ap.add_argument("--mongo", default=DEFAULT_MONGO_URL)
    ap.add_argument("--db", default=DEFAULT_DB_NAME)
    ap.add_argument("--min-size", type=float, default=1.0, help="min size GiB")
    args = ap.parse_args()

    global SIZE_MIN
    SIZE_MIN = int(args.min_size * 1024 * 1024 * 1024)

    roots = [Path(r) for r in args.roots]
    client = MongoClient(args.mongo)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Tuple[str, str, str, str]] = []
    for root in roots:
        total = count_candidates(root)
        pbar = tqdm(total=total, desc=f"Scanning {root}", unit="file")
        processed = 0
        for abspath in _walk_candidates(root):
            try:
                rel = abspath.relative_to(root).as_posix()
            except Exception:
                rel = abspath.as_posix()
            code = detect_code_from_filename(abspath) or ""
            href = mongo_find_href_by_code(client, args.db, code) if code else None
            rows.append((root.as_posix(), rel, code, href or ""))
            processed += 1
            pbar.update(1)
        pbar.close()

    headers = ["root", "relpath", "code", "href"]

    # Load existing CSV (if any) to avoid duplicates by (root, relpath)
    existing_rows: list[tuple[str, str, str, str]] = []
    key_set: set[tuple[str, str]] = set()
    if outp.exists():
        try:
            if pd is not None:
                df_old = pd.read_csv(outp)
                for _, r in df_old.iterrows():
                    root_v = str(r.get("root", ""))
                    rel_v = str(r.get("relpath", ""))
                    code_v = str(r.get("code", "")) if not pd.isna(r.get("code")) else ""
                    href_v = str(r.get("href", "")) if not pd.isna(r.get("href")) else ""
                    existing_rows.append((root_v, rel_v, code_v, href_v))
                    key_set.add((root_v, rel_v))
            else:
                with open(outp, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        root_v = r.get("root", "")
                        rel_v = r.get("relpath", "")
                        code_v = r.get("code", "")
                        href_v = r.get("href", "")
                        existing_rows.append((root_v, rel_v, code_v, href_v))
                        key_set.add((root_v, rel_v))
        except Exception:
            # If file unreadable, ignore previous contents
            existing_rows = []
            key_set = set()

    # Merge new rows, de-duplicated by (root, relpath)
    added = 0
    for row in rows:
        key = (row[0], row[1])
        if key not in key_set:
            existing_rows.append(row)
            key_set.add(key)
            added += 1

    # Sort by code ascending, then root and relpath for stability
    existing_rows.sort(key=lambda x: ((x[2] or "").upper(), x[0], x[1]))

    if pd is not None:
        df = pd.DataFrame(existing_rows, columns=headers)
        df.to_csv(outp, index=False)
    else:
        with open(outp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(existing_rows)

    print(f"Done. Scanned {len(rows)} files; added {added} new rows. CSV written to {outp}")


if __name__ == "__main__":
    main()
