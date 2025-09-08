from __future__ import annotations

"""
Capture periodic screenshots from movie videos and save paths into MongoDB.

Single movie mode:
  python script/db/capture_screenshots.py --href /v/96WDRV --dst-root /Volumes/images/jdb \
      --start 5 --interval 60 --max-frames 12 --ffmpeg ffmpeg --ffprobe ffprobe

Batch mode (default workers=5):
  python script/db/capture_screenshots.py --dst-root /Volumes/images/jdb --batch \
      --workers 6 --start 5 --interval 60 --max-frames 12

Behavior
- Stores images under: <dst-root>/screenshot/<href.strip('/')>/<code>_<sec>.jpg
- Saves to DB as '/screenshot/<href.strip('/')>/<code>_<sec>.jpg' list in field 'screenshot3'.
- Adds status.screenshot3_done = true and status.screenshot3_at timestamp.
- Skips docs already marked done unless --force is given.
"""

import argparse
import datetime as dt
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pymongo import MongoClient
from tqdm import tqdm


def run_ffprobe_duration(ffprobe_path: str, video_path: str) -> Optional[float]:
    try:
        out = subprocess.check_output(
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            timeout=30,
        )
        return float(out.decode("utf-8").strip())
    except Exception:
        return None


def ensure_paths(dst_root: Path, href: str, code: str, sec: int) -> tuple[str, Path]:
    rel_store = f"/screenshot/{href.strip('/')}/{code}_{sec}.jpg"
    fs_path = dst_root / rel_store.lstrip("/")
    fs_path.parent.mkdir(parents=True, exist_ok=True)
    return rel_store, fs_path


def capture_one_frame(
    ffmpeg_path: str, video_path: str, sec: int, out_path: Path
) -> bool:
    try:
        # -y overwrite; -ss before -i for faster seek (keyframe accuracy is good enough for thumbs)
        subprocess.check_call(
            [
                ffmpeg_path,
                "-ss",
                str(sec),
                "-i",
                video_path,
                "-frames:v",
                "1",
                "-q:v",
                "2",
                "-y",
                str(out_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        return out_path.exists()
    except Exception:
        return False


def times_from_duration(
    start: int, interval: int, duration: Optional[float], max_frames: Optional[int]
) -> List[int]:
    secs: List[int] = []
    cur = max(0, int(start))
    count = 0
    limit = int(duration or 0)
    while True:
        if max_frames is not None and count >= max_frames:
            break
        if duration is not None and cur >= limit:
            break
        secs.append(cur)
        count += 1
        cur += int(interval)
        # safety upper bound if no duration provided
        if duration is None and max_frames is None and count >= 10:
            break
    return secs


def process_movie_doc(
    doc: Dict[str, Any],
    *,
    dst_root: Path,
    ffmpeg_path: str,
    ffprobe_path: str,
    start: int,
    interval: int,
    max_frames: Optional[int],
    progress: Optional[callable] = None,
) -> Dict[str, Any]:
    href = doc.get("href") or ""
    code = (doc.get("code") or "").strip() or "movie"
    v = doc.get("video") or {}
    video_path = (
        v.get("abs_path")
        or (Path(v.get("root", "")) / Path(v.get("path", ""))).as_posix()
    )
    if not video_path:
        return {"href": href, "paths": [], "ok": False, "reason": "no_video_path"}
    if not Path(video_path).exists():
        return {"href": href, "paths": [], "ok": False, "reason": "video_missing"}
    duration = v.get("duration_seconds")
    if not duration:
        duration = run_ffprobe_duration(ffprobe_path, video_path)

    secs = times_from_duration(start, interval, duration, max_frames)
    saved: List[str] = []
    for s in secs:
        rel_store, fs_path = ensure_paths(dst_root, href, code, s)
        ok = capture_one_frame(ffmpeg_path, video_path, s, fs_path)
        if ok:
            saved.append(rel_store)
        if progress:
            try:
                progress(1)
            except Exception:
                pass
    if not saved:
        return {
            "href": href,
            "paths": [],
            "ok": False,
            "reason": "ffmpeg_failed",
            "total": len(secs),
        }
    return {"href": href, "paths": saved, "ok": True, "total": len(secs)}


def main():
    ap = argparse.ArgumentParser(description="Capture screenshots for movies")
    ap.add_argument("--href", help="single movie href")
    ap.add_argument("--batch", action="store_true", help="process movies in batch")
    ap.add_argument("--dst-root", required=True, help="destination root for images")
    ap.add_argument(
        "--mongo",
        default=os.getenv(
            "MONGO_URL", "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
        ),
    )
    ap.add_argument("--db", default=os.getenv("MONGO_DB_NAME", "jdb"))
    ap.add_argument("--start", type=int, default=5)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--ffmpeg", default=os.getenv("FFMPEG", "ffmpeg"))
    ap.add_argument("--ffprobe", default=os.getenv("FFPROBE", "ffprobe"))
    ap.add_argument(
        "--force", action="store_true", help="recreate even if already done"
    )
    args = ap.parse_args()

    client = MongoClient(args.mongo)
    col = client[args.db]["movies"]
    dst_root = Path(args.dst_root)

    def update_doc(
        href: str, paths: List[str], *, ok: bool, reason: Optional[str] = None
    ):
        if ok:
            # merge unique with any existing screenshot3
            doc = col.find_one({"href": href}, projection={"screenshot3": 1}) or {}
            cur = list(doc.get("screenshot3") or [])
            seen = set(cur)
            merged = cur[:]
            for p in paths:
                if p not in seen:
                    merged.append(p)
                    seen.add(p)
            col.update_one(
                {"href": href},
                {
                    "$set": {
                        "screenshot3": merged,
                        "status.screenshot3_done": True,
                        "status.screenshot3_at": dt.datetime.now(dt.UTC),
                    },
                    "$unset": {"status.screenshot3_error": ""},
                },
            )
        else:
            col.update_one(
                {"href": href},
                {
                    "$set": {
                        "status.screenshot3_done": False,
                        "status.screenshot3_error": reason or "unknown",
                        "status.screenshot3_at": dt.datetime.utcnow(),
                    }
                },
            )

    if args.href and not args.batch:
        doc = col.find_one({"href": args.href})
        if not doc:
            print("movie not found")
            return
        if not args.force and (doc.get("status", {}).get("screenshot3_done") is True):
            print("already done; use --force to redo")
            return
        # per-movie progress bar
        v = doc.get("video") or {}
        duration = v.get("duration_seconds") or run_ffprobe_duration(
            args.ffprobe, (v.get("abs_path") or "")
        )
        secs_preview = times_from_duration(
            args.start, args.interval, duration, args.max_frames
        )
        from tqdm import tqdm as _tqdm

        pbar = _tqdm(total=len(secs_preview), desc=f"1/1", unit="frame")
        pbar.set_postfix_str(str(doc.get("href")))
        res = process_movie_doc(
            doc,
            dst_root=dst_root,
            ffmpeg_path=args.ffmpeg,
            ffprobe_path=args.ffprobe,
            start=args.start,
            interval=args.interval,
            max_frames=args.max_frames,
            progress=pbar.update,
        )
        pbar.close()
        update_doc(
            res.get("href", ""),
            res.get("paths", []),
            ok=res.get("ok", False),
            reason=res.get("reason"),
        )
        if res.get("ok"):
            print(f"Done {res.get('href')}: {len(res.get('paths', []))} shots")
        else:
            print(f"Skip {res.get('href')}: {res.get('reason')}")
        return

    # batch
    q: Dict[str, Any] = {"video": {"$exists": True, "$type": "object"}}
    if not args.force:
        q["$or"] = [
            {"status.screenshot3_done": {"$exists": False}},
            {"status.screenshot3_done": {"$ne": True}},
        ]
    docs = list(col.find(q, projection={"href": 1, "code": 1, "video": 1}).limit(5000))
    if not docs:
        print("No candidates")
        return

    results: List[Dict[str, Any]] = []
    total_tasks = len(docs)
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [
            ex.submit(
                process_movie_doc,
                d,
                dst_root=dst_root,
                ffmpeg_path=args.ffmpeg,
                ffprobe_path=args.ffprobe,
                start=args.start,
                interval=args.interval,
                max_frames=args.max_frames,
            )
            for d in docs
        ]
        pbar = tqdm(
            total=total_tasks, desc=f"剩余 {total_tasks}/{total_tasks}", unit="mv"
        )
        for f in as_completed(futs):
            try:
                r = f.result()
                # immediate DB update per movie
                update_doc(
                    r.get("href", ""),
                    r.get("paths", []),
                    ok=r.get("ok", False),
                    reason=r.get("reason"),
                )
                results.append(r)
                done += 1
                pbar.update(1)
                href_disp = str(r.get("href", ""))
                pbar.set_description(f"剩余 {total_tasks-done}/{total_tasks}")
                pbar.set_postfix({"href": href_disp})
            except Exception:
                pass
        pbar.close()
    print(f"Batch done: {len(results)} movies")


if __name__ == "__main__":
    main()
