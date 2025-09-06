from __future__ import annotations

import argparse
import os
import sys
import traceback
from typing import Optional

import requests

try:
    # Reuse parser from the crawler module
    from script.javdb.actors_censored import _parse_actors, _is_blocked
except Exception:
    # Fall back to relative import if executed as module
    from javdb.actors_censored import _parse_actors, _is_blocked  # type: ignore


def _cookie_header(cookie: Optional[str]) -> Optional[str]:
    if not cookie:
        return None
    if cookie.lower().startswith("cookie:"):
        return cookie.split(":", 1)[1].strip()
    return cookie


def load_html_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fetch_html(url: str, *, cookie: Optional[str] = None, proxy: Optional[str] = None, timeout: int = 20) -> str:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    if cookie:
        session.headers["Cookie"] = _cookie_header(cookie)  # type: ignore
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def main() -> int:
    parser = argparse.ArgumentParser(description="Test: fetch one actors page and parse actors")
    parser.add_argument("--url", default=None, help="Actors page URL, e.g. https://.../actors/censored?page=1")
    parser.add_argument("--file", default=None, help="Local HTML file path for testing")
    parser.add_argument("--cookie", default=None, help="Cookie header string for authenticated requests")
    parser.add_argument("--cookie-file", default=None, help="Path to cookie file (raw header or name=value lines)")
    parser.add_argument("--proxy", default=None, help="HTTP(S) proxy, e.g. http://127.0.0.1:7890")

    args = parser.parse_args()

    # Resolve cookie from file if provided
    cookie_val = args.cookie
    if not cookie_val and args.cookie_file and os.path.exists(args.cookie_file):
        try:
            from script.clawer import _parse_cookie_file_or_string, USEFUL_COOKIE_KEYS  # reuse helper
            with open(args.cookie_file, "r", encoding="utf-8") as f:
                raw = f.read()
            cookie_val = _parse_cookie_file_or_string(raw, only_keys=USEFUL_COOKIE_KEYS)
        except Exception:
            # If helper not available, just read raw content
            with open(args.cookie_file, "r", encoding="utf-8") as f:
                cookie_val = f.read().strip()

    try:
        if args.file:
            html = load_html_from_file(args.file)
        elif args.url:
            html = fetch_html(args.url, cookie=cookie_val, proxy=args.proxy)
        else:
            # Default to sample file for convenience
            default_path = os.path.join(os.path.dirname(__file__), "actors_sample.html")
            html = load_html_from_file(default_path)

        if _is_blocked(html):
            print("Blocked or challenge page detected.")
            return 2

        actors = _parse_actors(html)
        print(f"Parsed actors: {len(actors)}")
        for i, a in enumerate(actors[:10]):
            print(f"[{i+1}] name={a.get('name')} href={a.get('href')} avatar={a.get('avatar')}")
        return 0
    except Exception as e:
        print("ERROR while fetching/parsing one page:")
        print(e)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

