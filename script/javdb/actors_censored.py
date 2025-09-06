from __future__ import annotations

import os
import re
import time
import json
import random
import threading
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, ASCENDING
from concurrent.futures import ThreadPoolExecutor, as_completed

# Local helpers
from publisher import change_proxy as cp


DEFAULT_BASE = "https://javdb561.com"
DEFAULT_START = "/actors/censored"
DEFAULT_CONTROLLER = "http://127.0.0.1:9097"
DEFAULT_SECRET = "12345678"
DEFAULT_PROXY_ENDPOINT = "http://127.0.0.1:7890"
DEFAULT_MONGO_URL = "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
DEFAULT_DB = "jdb"
DEFAULT_COL = "actors"
BAN_FILE = os.path.join(os.path.dirname(__file__), "banned_proxies.txt")


def _ensure_mongo_collection(mongo_url: str, db_name: str, col_name: str):
    client = MongoClient(mongo_url)
    db = client[db_name]
    col = db[col_name]
    # Unique index on href
    try:
        col.create_index([("href", ASCENDING)], unique=True)
    except Exception:
        pass
    return col


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _cookie_header(cookie: Optional[str]) -> Optional[str]:
    if cookie and cookie.lower().startswith("cookie:"):
        return cookie.split(":", 1)[1].strip()
    return cookie


def _read_ban_list(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception:
        return []


def _append_ban(path: str, name: str) -> None:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(name + "\n")
    except Exception:
        pass


class ProxyRotator:
    def __init__(
        self,
        *,
        controller_url: str = DEFAULT_CONTROLLER,
        group_name: Optional[str] = None,
        secret: Optional[str] = DEFAULT_SECRET,
        ban_file: str = BAN_FILE,
    ) -> None:
        self.controller_url = controller_url
        self.group_name = group_name
        self.secret = secret
        self.ban_file = ban_file
        self.lock = threading.Lock()
        self._banned = set(_read_ban_list(self.ban_file))
        self._proxies = self._fetch_all()
        self.current: Optional[str] = None

    def _fetch_all(self) -> List[str]:
        names = cp.get_all_proxy_name(controller_url=self.controller_url, secret=self.secret, group_name=self.group_name) or []
        return [n for n in names if n and n not in self._banned]

    def _switch(self, name: str) -> bool:
        try:
            return cp.switch_proxy(
                name,
                controller_url=self.controller_url,
                secret=self.secret,
                group_name=self.group_name,
            )
        except Exception:
            return False

    def ban(self, name: Optional[str]) -> None:
        if not name:
            return
        with self.lock:
            self._banned.add(name)
            _append_ban(self.ban_file, name)
            # remove from available list
            self._proxies = [p for p in self._proxies if p != name]
            if self.current == name:
                self.current = None

    def switch_random(self) -> Optional[str]:
        with self.lock:
            if not self._proxies:
                self._proxies = self._fetch_all()
            candidates = [p for p in self._proxies if p not in self._banned]
            if not candidates:
                return None
            name = random.choice(candidates)
        ok = self._switch(name)
        if ok:
            self.current = name
            return name
        else:
            # mark as banned to avoid re-trying immediately
            self.ban(name)
            return None


def _is_blocked(html: str) -> bool:
    if not html:
        return True
    low = html.lower()
    return (
        "just a moment" in low
        or "attention required" in low
        or "captcha" in low
        or "cloudflare" in low
    )


def _extract_pages(html: str) -> int:
    soup = _soup(html)
    pages = 1
    for a in soup.select("nav.pagination a[href]"):
        href = a.get("href", "")
        m = re.search(r"[?&]page=(\d+)", href)
        if m:
            try:
                pages = max(pages, int(m.group(1)))
            except Exception:
                pass
    return pages


def _parse_actors(html: str) -> List[Dict[str, Optional[str]]]:
    soup = _soup(html)
    out: List[Dict[str, Optional[str]]] = []
    for box in soup.select(".box.actor-box"):
        a = box.select_one("a[href]")
        if not a:
            continue
        href = a.get("href")
        title = a.get("title")
        strong = a.select_one("strong")
        name = strong.get_text(strip=True) if strong else None
        img = a.select_one("img.avatar")
        avatar = img.get("src") if img else None
        out.append({
            "title": title,
            "href": href,
            "avatar": avatar,
            "name": name,
        })
    return out


class TaskStore:
    def __init__(self, *, root_dir: str, category: str) -> None:
        os.makedirs(root_dir, exist_ok=True)
        self.tasks_file = os.path.join(root_dir, f"actors_tasks_{category}.txt")
        self.done_file = os.path.join(root_dir, f"actors_done_{category}.txt")
        self.lock = threading.Lock()
        self.tasks: set[str] = set()
        self.done: set[str] = set()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                self.tasks = {line.strip() for line in f if line.strip()}
        if os.path.exists(self.done_file):
            with open(self.done_file, "r", encoding="utf-8") as f:
                self.done = {line.strip() for line in f if line.strip()}

    def set_all_tasks(self, items: List[str]) -> None:
        with self.lock:
            self.tasks.update(items)
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(self.tasks)))

    def remaining(self) -> List[str]:
        with self.lock:
            return [t for t in self.tasks if t not in self.done]

    def mark_done(self, item: str) -> None:
        with self.lock:
            if item not in self.done:
                self.done.add(item)
                with open(self.done_file, "a", encoding="utf-8") as f:
                    f.write(item + "\n")


def crawl_actors(
    *,
    base: str = DEFAULT_BASE,
    start_path: str = DEFAULT_START,
    category: str = "censored",
    cookie: Optional[str] = None,
    workers: int = 1,
    controller_url: str = DEFAULT_CONTROLLER,
    group_name: Optional[str] = None,
    secret: Optional[str] = DEFAULT_SECRET,
    proxy_endpoint: str = DEFAULT_PROXY_ENDPOINT,
    mongo_url: str = DEFAULT_MONGO_URL,
    db_name: str = DEFAULT_DB,
    collection_name: str = DEFAULT_COL,
    start_page: int = 1,
    end_page: Optional[int] = None,
    max_pages: Optional[int] = None,
    stop_after_empty: int = 5,
    rotate_threshold: int = 5,
    rotate_cooldown: int = 30,
    sleep_per_page: int = 10,
) -> Dict[str, int]:
    base = base.rstrip("/")
    start_url = f"{base}{start_path}"

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    if cookie:
        session.headers["Cookie"] = _cookie_header(cookie)
    if proxy_endpoint:
        session.proxies.update({"http": proxy_endpoint, "https": proxy_endpoint})

    rotator = ProxyRotator(controller_url=controller_url, group_name=group_name, secret=secret)
    col = _ensure_mongo_collection(mongo_url, db_name, collection_name)

    # Build task store and seed tasks using direct ?page=N
    store = TaskStore(root_dir=os.path.dirname(__file__), category=category)
    all_tasks: List[str] = []

    if end_page is not None or max_pages is not None:
        sp = max(1, int(start_page))
        ep = int(end_page) if end_page is not None else sp + int(max_pages) - 1
        all_tasks = [f"{start_url}?page={p}" if p > 1 else start_url for p in range(sp, ep + 1)]
    else:
        # Probe sequentially until empty pages reach threshold; no rotation
        empty_streak = 0
        p = max(1, int(start_page))
        while True:
            url = f"{start_url}?page={p}" if p > 1 else start_url
            try:
                r = session.get(url, timeout=12)
                if r.ok and not _is_blocked(r.text):
                    actors = _parse_actors(r.text)
                    if actors:
                        all_tasks.append(url)
                        empty_streak = 0
                    else:
                        empty_streak += 1
                    if empty_streak >= stop_after_empty:
                        break
                    p += 1
                    continue
            except Exception:
                pass
            # backoff on error
            time.sleep(1)
        if not all_tasks:
            all_tasks.append(start_url)

    store.set_all_tasks(all_tasks)

    # Prepare local JSON output directory: ./result/actors/{category}
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_dir = os.path.join(repo_root, 'result', 'actors', category)
    os.makedirs(out_dir, exist_ok=True)

    def _page_number_from_url(u: str) -> int:
        m = re.search(r"[?&]page=(\d+)", u)
        return int(m.group(1)) if m else 1

    # Single worker sequential crawl with per-page delay (no proxy switching)
    total_saved = 0
    remaining = store.remaining()
    print(f"Remaining tasks: {len(remaining)}")
    max_retries = 3
    for url in remaining:
        success = False
        for _ in range(max_retries):
            try:
                r = session.get(url, timeout=20)
                if r.ok and not _is_blocked(r.text):
                    actors = _parse_actors(r.text)
                    # Save this page to local JSON file
                    try:
                        page_no = _page_number_from_url(url)
                        fpath = os.path.join(out_dir, f"page-{page_no}.json")
                        with open(fpath, 'w', encoding='utf-8') as f:
                            json.dump(actors, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"Write JSON failed for {url}: {e}")
                    ops = 0
                    for doc in actors:
                        href = doc.get("href")
                        if not href:
                            continue
                        doc["category"] = category
                        try:
                            col.update_one({"href": href}, {"$set": doc}, upsert=True)
                            ops += 1
                        except Exception:
                            pass
                    total_saved += ops
                    store.mark_done(url)
                    print(f"Done {url}: saved {ops}")
                    success = True
                    break
            except Exception:
                pass
            time.sleep(2)
        if not success:
            print(f"Give up {url}")
        # Enforce delay between pages
        time.sleep(max(0, int(sleep_per_page)))

    return {"tasks": len(all_tasks), "saved": total_saved}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Crawl JavDB actors list with proxy rotation and persistent tasks")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Base site, e.g. https://javdb561.com")
    parser.add_argument("--category", default="censored", choices=["censored", "uncensored", "western"], help="Actor category")
    parser.add_argument("--path", default=None, help="Start path; inferred from category if omitted")
    parser.add_argument("--cookie", default=None, help="Cookie header string")
    parser.add_argument("--cookie-file", default=None, help="Path to cookie file (name value lines or Cookie header)")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent workers (set to 1 for sequential crawl)")
    parser.add_argument("--controller", default=DEFAULT_CONTROLLER, help="Clash controller URL")
    parser.add_argument("--group", dest="group_name", default=None, help="Clash selector group name (rule/selector). Auto-detect if omitted")
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="Clash controller secret (Bearer)")
    parser.add_argument("--proxy", default=DEFAULT_PROXY_ENDPOINT, help="HTTP(S) proxy endpoint for requests")
    parser.add_argument("--mongo-url", default=DEFAULT_MONGO_URL, help="Mongo connection URL")
    parser.add_argument("--db", default=DEFAULT_DB, help="Mongo database name")
    parser.add_argument("--collection", default=DEFAULT_COL, help="Mongo collection name")
    parser.add_argument("--start-page", type=int, default=1, help="Start page number (default 1)")
    parser.add_argument("--end-page", type=int, default=None, help="End page number (inclusive)")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to crawl from start-page if end-page not set")
    parser.add_argument("--stop-after-empty", type=int, default=5, help="Stop scanning after N consecutive empty pages")
    parser.add_argument("--rotate-threshold", type=int, default=5, help="Rotate after this many blocked signals")
    parser.add_argument("--rotate-cooldown", type=int, default=30, help="Minimum seconds between rotations")
    parser.add_argument("--sleep", type=int, default=10, help="Seconds to sleep between pages (sequential mode)")

    args = parser.parse_args()

    # Resolve start path by category if not provided
    start_path = args.path
    if not start_path:
        start_path = "/actors/censored" if args.category == "censored" else ("/actors/uncensored" if args.category == "uncensored" else "/actors/western")

    cookie_val = args.cookie
    if not cookie_val and args.cookie_file and os.path.exists(args.cookie_file):
        from script.clawer import _parse_cookie_file_or_string, USEFUL_COOKIE_KEYS  # reuse

        with open(args.cookie_file, "r", encoding="utf-8") as f:
            raw = f.read()
        cookie_val = _parse_cookie_file_or_string(raw, only_keys=USEFUL_COOKIE_KEYS)

    stats = crawl_actors(
        base=args.base,
        start_path=start_path,
        category=args.category,
        cookie=cookie_val,
        workers=args.workers,
        controller_url=args.controller,
        group_name=args.group_name,
        secret=args.secret,
        proxy_endpoint=args.proxy,
        mongo_url=args.mongo_url,
        db_name=args.db,
        collection_name=args.collection,
        start_page=args.start_page,
        end_page=args.end_page,
        max_pages=args.max_pages,
        stop_after_empty=args.stop_after_empty,
        rotate_threshold=args.rotate_threshold,
        rotate_cooldown=args.rotate_cooldown,
        sleep_per_page=args.sleep,
    )
    print(json.dumps(stats, ensure_ascii=False))
