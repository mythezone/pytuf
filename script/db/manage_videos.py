from __future__ import annotations

"""
Manage local video files using the CSV produced by scan_videos_to_csv.py

Actions (can chain multiple via --actions a b c):
  - add_column: requires --column "name,default"; add the column if missing
  - clean: rename files whose filename contains '@' by removing the prefix
           before '@' and lowercasing the suffix; update relpath, code, href
  - check: remove CSV rows whose file no longer exists
  - update_db: write movie.video info back to Mongo for rows with href and not
               yet written; mark 'written' flag true after success
  - match: for rows without href, try to find href by code in DB
  - search: rescan given roots and append new files (skip ones already in CSV);
            during search, if filename contains '@', rename the physical file
            as in 'clean' before recording

Usage examples:
  python script/db/manage_videos.py --csv script/result/local_movie.csv \
    --actions add_column clean match update_db --column "note,"

  python script/db/manage_videos.py --csv script/result/local_movie.csv \
    --actions search --roots /Volumes/disk/D/Adult /Volumes/disk/G/Adult
"""

import argparse
import csv
import os
import platform
import re
import shutil
import subprocess
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tqdm import tqdm
from pymongo import MongoClient

import pandas as pd

VIDEO_EXTS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".wmv",
    ".mov",
    ".iso",
    ".ts",
    ".m2ts",
    ".flv",
    ".mpg",
    ".mpeg",
    ".webm",
}
SIZE_MIN = 1 * 1024 * 1024 * 1024
CODE_RE = re.compile(r"([A-Za-z]{2,8})[-_ ]?(\d{2,6}[A-Za-z]?)")
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


def detect_code_from_filename(path: Path) -> Optional[str]:
    name = path.stem
    m = CODE_RE.search(name)
    if not m:
        return None
    return f"{m.group(1).upper()}-{m.group(2).upper()}"


def mongo_find_href_by_code(
    client: MongoClient, db_name: str, code: str
) -> Optional[str]:
    letters, digits = _split_letters_digits(_canon(code) or "")
    if not letters or not digits:
        return None
    pattern = f"^{re.escape(letters)}[- ]?{re.escape(digits)}$"
    doc = client[db_name]["movies"].find_one(
        {"code": {"$regex": pattern, "$options": "i"}}, projection={"href": 1}
    )
    return doc.get("href") if doc else None


def ffprobe_metadata(
    path: Path, ffprobe_path: str = "ffprobe", timeout: int = 20
) -> Dict[str, Any]:
    try:
        cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        out = subprocess.check_output(cmd, timeout=timeout)
        info = json.loads(out.decode("utf-8", errors="ignore"))
        res: Dict[str, Any] = {}
        fmt = info.get("format", {})
        if fmt:
            if "duration" in fmt:
                try:
                    res["duration_seconds"] = float(fmt["duration"])  # seconds
                except Exception:
                    pass
            if "bit_rate" in fmt:
                try:
                    res["bitrate"] = int(fmt["bit_rate"])  # bps
                except Exception:
                    pass
        vcodec = None
        acodec = None
        width = height = None
        for s in info.get("streams", []) or []:
            if s.get("codec_type") == "video" and vcodec is None:
                vcodec = s.get("codec_name")
                width = s.get("width")
                height = s.get("height")
            elif s.get("codec_type") == "audio" and acodec is None:
                acodec = s.get("codec_name")
        if vcodec:
            res["video_codec"] = vcodec
        if acodec:
            res["audio_codec"] = acodec
        if width and height:
            res["width"] = int(width)
            res["height"] = int(height)
        return res
    except Exception:
        return {}


def load_csv(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    if pd is not None and path.exists():
        df = pd.read_csv(path)
        rows = df.to_dict(orient="records")  # type: ignore
        cols = list(df.columns)
        return rows, cols
    cols = []
    rows: List[Dict[str, Any]] = []
    if path.exists():
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = list(reader.fieldnames or [])
            for r in reader:
                rows.append(dict(r))
    return rows, cols


def save_csv(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    # ensure all columns
    for r in rows:
        for c in columns:
            if c not in r:
                r[c] = ""

    # sort by code then root/relpath if present
    def _key(r: Dict[str, Any]):
        return (
            (str(r.get("code") or "")).upper(),
            str(r.get("root") or ""),
            str(r.get("relpath") or ""),
        )

    rows_sorted = sorted(rows, key=_key)
    if pd is not None:
        df = pd.DataFrame(rows_sorted, columns=columns)
        df.to_csv(path, index=False)
    else:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=columns)
            w.writeheader()
            w.writerows(rows_sorted)


def walk_candidates(root: Path) -> List[Path]:
    cands: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in VIDEO_EXTS:
                continue
            try:
                if p.stat().st_size < SIZE_MIN:
                    continue
            except OSError:
                continue
            cands.append(p)
    return cands


def safe_rename(old: Path, new: Path) -> Path:
    new.parent.mkdir(parents=True, exist_ok=True)
    target = new
    if target.exists():
        # avoid overwrite; add numeric suffix
        base = new.stem
        ext = new.suffix
        i = 1
        while target.exists():
            target = new.with_name(f"{base}_{i}{ext}")
            i += 1
    try:
        shutil.move(str(old), str(target))
        return target
    except Exception:
        return old


def main():
    ap = argparse.ArgumentParser(description="Manage local videos from CSV results")
    ap.add_argument(
        "--csv",
        default="./result/local_movie.csv",
        help="results CSV path",
    )
    ap.add_argument(
        "--actions",
        nargs="+",
        required=True,
        choices=["add_column", "clean", "check", "update_db", "match", "search"],
        help="actions to run in order",
    )
    ap.add_argument("--column", default="", help="for add_column: 'name,default' ")
    ap.add_argument(
        "--mongo",
        default=os.getenv(
            "MONGO_URL", "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
        ),
    )
    ap.add_argument("--db", default=os.getenv("MONGO_DB_NAME", "jdb"))
    ap.add_argument("--ffprobe", default=os.getenv("FFPROBE", "ffprobe"))
    ap.add_argument("--no-probe", action="store_true")
    ap.add_argument("--roots", nargs="*", default=[], help="roots for search action")
    ap.add_argument(
        "--min-size", type=float, default=1.0, help="min size GiB for search"
    )
    args = ap.parse_args()

    global SIZE_MIN
    SIZE_MIN = int(args.min_size * 1024 * 1024 * 1024)

    csv_path = Path(args.csv)
    rows, cols = load_csv(csv_path)
    if not rows and "root" not in cols:
        # create empty structure with standard columns
        cols = ["root", "relpath", "code", "href", "written"]

    # Ensure standard 'written' column exists
    if "written" not in cols:
        cols.append("written")
        for r in rows:
            r["written"] = ""
    # Ensure 'status' column exists for recording per-row errors
    if "status" not in cols:
        cols.append("status")
        for r in rows:
            r["status"] = ""

    client = MongoClient(args.mongo)

    for action in args.actions:
        if action == "add_column":
            if args.column and "," in args.column:
                name, default = args.column.split(",", 1)
                name = name.strip()
                if name and name not in cols:
                    cols.append(name)
                    for r in rows:
                        r[name] = default
            else:
                print("--column must be provided as 'name,default'")

        elif action == "clean":
            changed = 0
            for r in tqdm(rows, desc="Clean", unit="row"):
                root = Path(r.get("root") or "")
                rel = Path(r.get("relpath") or "")
                if not rel.name or "@" not in rel.name:
                    continue
                old_abs = root / rel
                if not old_abs.exists():
                    continue
                # new filename: take suffix after last '@', lowercase
                new_name = rel.name.split("@")[-1]
                new_name = new_name.lower()
                new_abs = old_abs.with_name(new_name)
                final_abs = safe_rename(old_abs, new_abs)
                # update row
                new_rel = final_abs.relative_to(root)
                r["relpath"] = new_rel.as_posix()
                # update code + href
                code = detect_code_from_filename(final_abs) or ""
                r["code"] = code
                r["href"] = mongo_find_href_by_code(client, args.db, code) or ""
                changed += 1
            print(f"Clean: updated {changed} rows")

        elif action == "check":
            before = len(rows)
            rows = [
                r
                for r in rows
                if (Path(r.get("root") or "") / Path(r.get("relpath") or "")).exists()
            ]
            print(f"Check: removed {before - len(rows)} missing files")

        elif action == "update_db":
            updated = 0
            # columns to save during streaming updates
            save_columns = list(
                dict.fromkeys(
                    cols + ["root", "relpath", "code", "href", "written", "status"]
                )
            )
            for r in tqdm(rows, desc="Update DB", unit="row"):
                # Robust href extraction with error capture
                try:
                    href_val = r.get("href")
                    href = (
                        href_val if isinstance(href_val, str) else str(href_val or "")
                    ).strip()
                except Exception as e:
                    r["status"] = f"href_parse_error:{type(r.get('href')).__name__}"
                    # save immediately and skip
                    save_csv(csv_path, rows, save_columns)
                    continue
                if not href:
                    # still save checkpoint and continue
                    save_csv(csv_path, rows, save_columns)
                    continue
                if str(r.get("written") or "").lower() in ("1", "true", "yes"):
                    # already written; still checkpoint
                    save_csv(csv_path, rows, save_columns)
                    continue
                root = Path(r.get("root") or "")
                rel = Path(r.get("relpath") or "")
                abspath = root / rel
                info: Dict[str, Any] = {
                    "root": str(root),
                    "path": rel.as_posix(),
                    "abs_path": abspath.as_posix(),
                }
                try:
                    info["size_bytes"] = int(abspath.stat().st_size)
                except Exception:
                    info["size_bytes"] = None
                if not args.no_probe and abspath.exists():
                    info.update(ffprobe_metadata(abspath, ffprobe_path=args.ffprobe))
                res = client[args.db]["movies"].update_one(
                    {"href": href}, {"$set": {"video": info}}
                )
                if res.matched_count:
                    updated += 1
                    r["written"] = "1"
                # Save after each processed row to prevent duplicate writes on interruption
                save_csv(csv_path, rows, save_columns)
            print(f"Update DB: updated {updated} docs")

        elif action == "match":
            changed = 0
            for r in tqdm(rows, desc="Match", unit="row"):
                if r.get("href"):
                    continue
                code = r.get("code") or ""
                if not code:
                    # try detect from filename
                    root = Path(r.get("root") or "")
                    rel = Path(r.get("relpath") or "")
                    code = detect_code_from_filename(root / rel) or ""
                    r["code"] = code
                if not code:
                    continue
                href = mongo_find_href_by_code(client, args.db, code)
                if href:
                    r["href"] = href
                    changed += 1
            print(f"Match: set href for {changed} rows")

        elif action == "search":
            # Need roots; if not provided, choose OS-specific defaults
            roots = [Path(p) for p in (args.roots or [])]
            if not roots:
                if platform.system() == "Darwin":
                    roots = [
                        Path("/Volumes/disk/D/Adult"),
                        Path("/Volumes/disk/G/Adult"),
                    ]
                else:
                    roots = [Path("/mnt/disk1/Adult"), Path("/mnt/disk2/Adult")]
            # existing key set
            key_set = {(str(r.get("root")), str(r.get("relpath"))) for r in rows}
            added = 0
            for root in roots:
                cands = walk_candidates(root)
                for p in tqdm(cands, desc=f"Search {root}", unit="file"):
                    # rename on the fly if contains '@'
                    final_p = p
                    if "@" in p.name:
                        new_name = p.name.split("@")[-1].lower()
                        final_p = safe_rename(p, p.with_name(new_name))
                    try:
                        rel = final_p.relative_to(root).as_posix()
                    except Exception:
                        rel = final_p.as_posix()
                    key = (root.as_posix(), rel)
                    if key in key_set:
                        continue
                    code = detect_code_from_filename(final_p) or ""
                    href = (
                        mongo_find_href_by_code(client, args.db, code) if code else None
                    )
                    rows.append(
                        {
                            "root": root.as_posix(),
                            "relpath": rel,
                            "code": code,
                            "href": href or "",
                            "written": "",
                        }
                    )
                    key_set.add(key)
                    added += 1
            print(f"Search: added {added} new files")

    # Save back
    save_columns = list(
        dict.fromkeys(cols + ["root", "relpath", "code", "href", "written"])
    )
    save_csv(csv_path, rows, save_columns)
    print(f"Done. Actions executed: {' '.join(args.actions)}. Saved {csv_path}")


if __name__ == "__main__":
    main()
