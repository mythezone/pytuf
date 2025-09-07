from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import os

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
from base import BaseScraper, MongoDB

# keep consistent with actor.py
base_url = "https://javdb561.com"


@dataclass
class VideoDetail:
    # identity
    id: Optional[str]
    code: Optional[str]
    title: Optional[str]

    # links
    canonical_url: Optional[str]
    href_path: Optional[str]
    # removed composed hrefs map per latest requirement

    # media
    cover: Optional[str]
    cover_full: Optional[str]
    screenshots: List[str]

    # meta
    date: Optional[str]
    duration_minutes: Optional[int]
    duration_text: Optional[str]
    maker: Optional[Dict[str, Any]]
    publisher: Optional[Dict[str, Any]]
    series: Optional[Dict[str, Any]]
    categories: List[Dict[str, Any]]
    actors: List[Dict[str, Any]]
    rating: Optional[float]
    rating_count: Optional[int]
    stats: Dict[str, Optional[int]]

    # magnets and tabs
    magnets: List[Dict[str, Any]]
    reviews: List[Dict[str, Any]]
    related_lists: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    review_tab_url: Optional[str] = None
    related_lists_url: Optional[str] = None

    # source/debug
    source: str = "javdb"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def _extract_code_from_title(soup: BeautifulSoup) -> Optional[str]:
    # Prefer first <strong> inside h2.title
    h2 = soup.select_one(".video-detail h2.title") or soup.select_one("h2.title")
    if h2:
        strongs = h2.select("strong")
        if strongs:
            # text like: "ABF-265 "
            code = re.sub(r"\s+", "", _text(strongs[0]))
            # Normalize common hyphen/space variants
            code = code.replace("_", "-")
            m = re.search(r"([A-Za-z0-9]{2,}-?\d{2,})", code)
            if m:
                return m.group(1).upper().replace(" ", "")
    # Fallback: find in any element containing 番號
    for blk in soup.select(".video-detail .panel-block"):
        label = _text(blk.select_one("strong"))
        if "番號" in label:
            value = _text(blk.select_one(".value"))
            m = re.search(r"([A-Za-z0-9]{2,})\s*-\s*(\d{2,})", value)
            if m:
                return f"{m.group(1).upper()}-{m.group(2)}"
    return None


def _parse_rating(text: str) -> Tuple[Optional[float], Optional[int]]:
    # "4.19分, 由71人評價"
    if not text:
        return None, None
    score = None
    count = None
    m1 = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*分", text)
    if m1:
        try:
            score = float(m1.group(1))
        except Exception:
            score = None
    m2 = re.search(r"由\s*([0-9,]+)\s*人", text)
    if m2:
        try:
            count = int(m2.group(1).replace(",", ""))
        except Exception:
            count = None
    return score, count


def _parse_duration(text: str) -> Tuple[Optional[int], Optional[str]]:
    if not text:
        return None, None
    m = re.search(r"(\d+)", text)
    return (int(m.group(1)) if m else None, text.strip())


def _safe_href(el) -> Optional[str]:
    return el.get("href") if el else None


def _safe_src(el) -> Optional[str]:
    return el.get("src") if el else None


def _find_tab_url(soup: BeautifulSoup, *, tab_class: str) -> Optional[str]:
    a = soup.select_one(f"a.{tab_class}[data-url]")
    if a:
        return a.get("data-url")
    return None


def _parse_size_bytes(size_text: str) -> Optional[int]:
    if not size_text:
        return None
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]B)", size_text, re.I)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).upper()
    power = {"KB": 1, "MB": 2, "GB": 3, "TB": 4, "PB": 5}.get(unit, None)
    if power is None:
        return None
    return int(val * (1024 ** power))


def _parse_magnets(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in soup.select("#magnets-content .item"):
        name = None
        meta_text = None
        size_bytes = None
        file_count = None
        tags: List[str] = []
        magnet = None
        date_text = None

        a = item.select_one(".magnet-name a[href^='magnet:']")
        if a:
            magnet = a.get("href")
            name_el = a.select_one(".name")
            name = _text(name_el)
            meta_el = a.select_one(".meta")
            meta_text = _text(meta_el)
            size_bytes = _parse_size_bytes(meta_text)
            m_files = re.search(r"(\d+)\s*個?文件", meta_text)
            if m_files:
                try:
                    file_count = int(m_files.group(1))
                except Exception:
                    file_count = None
            for t in a.select(".tags .tag"):
                t_text = _text(t)
                if t_text:
                    tags.append(t_text)

        time_el = item.select_one(".date .time")
        if time_el:
            date_text = _text(time_el)

        results.append(
            {
                "magnet": magnet,
                "name": name,
                "meta_text": meta_text,
                "size_bytes": size_bytes,
                "file_cont": file_count,
                "tags": tags,
                "date": date_text,
            }
        )
    return results


def _origin(url: str) -> Optional[str]:
    try:
        p = urlparse(url)
        if p.scheme and p.netloc:
            return f"{p.scheme}://{p.netloc}"
    except Exception:
        return None
    return None


def _parse_cookie_file_or_string(data: str, *, only_keys: Optional[List[str]] = None) -> str:
    """Accept either a raw Cookie header string, or multi-line cookie export.

    - If data contains ';' and '=' on a single line, assume it's already a header.
    - Else, parse each non-empty line as whitespace/tab-separated columns: name, value, ...
    - If only_keys is provided, filter to those cookie names.
    """
    data = data.strip()
    if not data:
        return ""
    if (';' in data and '=' in data and '\n' not in data) or data.lower().startswith('cookie:'):
        # Looks like header already
        header = data
        if header.lower().startswith('cookie:'):
            header = header.split(':', 1)[1].strip()
        return header

    cookies: Dict[str, str] = {}
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Handle simple key=value lines first
        if '=' in line and ('\t' not in line and '  ' not in line):
            # e.g. over18=1
            key, val = line.split('=', 1)
            cookies[key.strip()] = val.strip()
            continue
        # Tab-or-space separated export where first two columns are name and value
        parts = [p for p in re.split(r"\s+|\t+", line) if p]
        if len(parts) >= 2:
            name = parts[0]
            val = parts[1]
            cookies[name] = val
    if only_keys:
        cookies = {k: v for k, v in cookies.items() if k in only_keys}
    return '; '.join(f"{k}={v}" for k, v in cookies.items())


def _parse_reviews_html(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict[str, Any]] = []
    # Heuristic: review items could be in .review-item, .review, or article.media
    items = soup.select(".review-item, .review, article.media") or soup.select(".columns .column .media")
    for el in items:
        # Score: count stars or read numeric
        score = None
        stars = el.select(".score-stars i.icon-star")
        if stars:
            score = float(len([s for s in stars if 'gray' not in (s.get('class') or [])]))
        else:
            m = re.search(r"([1-5](?:\.\d)?)", el.get_text(" ") or "")
            try:
                score = float(m.group(1)) if m else None
            except Exception:
                score = None

        content_el = el.select_one(".content, .review-content, .text, p")
        content = _text(content_el)
        out.append({"content": content or None, "score": score})
    return out


def _parse_related_lists_from_soup(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    # Prefer within the lists tab container
    containers = soup.select("#lists .plain-grid-list, .plain-grid-list")
    anchors = []
    if containers:
        for c in containers:
            anchors.extend(c.select("a[href*='/lists/']"))
    else:
        # Fallback: any anchor inside #lists
        anchors = soup.select("#lists a[href*='/lists/']")
    for a in anchors:
        name_el = a.select_one("strong")
        name = _text(name_el) or _text(a)
        href = _safe_href(a)
        if href:
            out.append({"name": name or None, "href": href})
    return out


def _parse_related_lists_html(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    return _parse_related_lists_from_soup(soup)


def _fetch_paginated(session: requests.Session, start_url: str, parse_items, *, timeout: int = 15, max_pages: int = 10) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen = set()
    url = start_url
    pages = 0
    while url and url not in seen and pages < max_pages:
        seen.add(url)
        pages += 1
        try:
            r = session.get(url, timeout=timeout)
            if not r.ok:
                break
            html = r.text
            items = parse_items(html)
            if items:
                results.extend(items)
            soup = BeautifulSoup(html, "html.parser")
            nxt = soup.select_one("nav.pagination a.pagination-next[href]")
            if nxt and nxt.get("href"):
                url = urljoin(url, nxt.get("href"))
            else:
                url = None
        except Exception:
            break
    return results


def _parse_recommendations(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    # Locate the panel whose header contains '你可能也喜歡'
    for panel in soup.select("article.message.video-panel"):
        header = panel.select_one(".message-header")
        if header and ("你可能也喜歡" in header.get_text() or "你可能也喜欢" in header.get_text()):
            for a in panel.select(".tile-images .tile-item"):
                href = _safe_href(a)
                img = a.select_one("img[src]")
                cover = _safe_src(img)
                code_el = a.select_one(".video-number")
                rid = _text(code_el) or None
                title_el = a.select_one(".video-title")
                title = _text(title_el) or a.get("title") or None
                if rid or title or cover:
                    out.append({
                        "id": rid,
                        "title": title,
                        "cover": cover,
                        "href": href,
                    })
            break
    return out


def parse_url(
    url: str,
    *,
    base_domains: Optional[List[str]] = None,
    fetch_tabs: bool = False,
    timeout: int = 15,
    headers: Optional[Dict[str, str]] = None,
    cookie: Optional[str] = None,
) -> Dict[str, Any]:
    headers = headers or {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    session = requests.Session()
    session.headers.update(headers)
    if cookie:
        session.headers["Cookie"] = cookie
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    detail = parse_video_detail_html(resp.text, base_domains=base_domains)

    if fetch_tabs:
        # Determine base origin for joining relative tab URLs
        base_origin = _origin(detail.canonical_url or url)
        if not base_origin:
            # fallback: body data-domain
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                dom = soup.select_one("body").get("data-domain") if soup.select_one("body") else None
            except Exception:
                dom = None
            base_origin = dom or base_domains[0] if base_domains else None

        # use the same session (with headers/cookie) for tab fetching
        # Reviews (with pagination if available)
        if detail.review_tab_url and base_origin:
            try:
                rurl = urljoin(base_origin, detail.review_tab_url)
                # fetch paginated reviews using the same pagination parser
                def parse_reviews(html: str):
                    return _parse_reviews_html(html)
                detail.reviews = _fetch_paginated(session, rurl, parse_reviews, timeout=timeout)
            except Exception:
                pass
        # Related lists (with pagination)
        if detail.related_lists_url and base_origin:
            try:
                lurl = urljoin(base_origin, detail.related_lists_url)
                rl = _fetch_paginated(session, lurl, _parse_related_lists_html, timeout=timeout)
                if rl:
                    # merge with any initial lists, unique by href
                    by_href = {x.get("href"): x for x in (detail.related_lists or []) if x.get("href")}
                    for it in rl:
                        h = it.get("href")
                        if h and h not in by_href:
                            by_href[h] = it
                    detail.related_lists = list(by_href.values())
            except Exception:
                pass

    return detail.to_dict()

def parse_video_detail_html(
    html: str,
    *,
    base_domains: Optional[List[str]] = None,
) -> VideoDetail:
    """
    解析 JavDB 详情页(示例见 script/sample.html)为结构化 JSON。

    - 在 video-detail 容器内提取影片信息。
    - 以标题中的番號作为 id/code。
    - 提取 canonical 并生成多主站 hrefs（可配置）。
    - 对缺失字段保持容错，返回 None/空列表。
    """
    base_domains = base_domains or [
        "https://javdb.com",
        "https://javdb561.com",
    ]
    soup = BeautifulSoup(html, "html.parser")

    root = soup.select_one(".video-detail") or soup

    # Title + code
    code = _extract_code_from_title(root)
    title_el = root.select_one(".video-detail h2.title .current-title") or root.select_one(
        "h2.title .current-title"
    )
    title = _text(title_el) or None

    # Canonical + hrefs
    canonical_url = None
    href_path = None
    link_canonical = soup.select_one("link[rel=canonical]")
    if link_canonical and link_canonical.get("href"):
        canonical_url = link_canonical.get("href")
        try:
            # Extract path only
            href_path = re.sub(r"^https?://[^/]+", "", canonical_url)
        except Exception:
            href_path = None
    if not href_path:
        # Fallback: body data-domain + window location path not available in static; try current path detection
        # As a last resort, try locate any link under breadcrumb-like anchors containing '/v/'
        a_v = soup.select_one("a[href^='/v/']")
        href_path = a_v.get("href") if a_v else None

    # hrefs composed map removed

    # Cover images
    cover_full = _safe_href(root.select_one(".column-video-cover a[href]"))
    cover = _safe_src(root.select_one("img.video-cover"))

    # Panel fields
    maker = publisher = series = None
    date = None
    duration_minutes = None
    duration_text = None
    rating = None
    rating_count = None
    categories: List[Dict[str, Any]] = []
    actors: List[Dict[str, Any]] = []

    # Iterate all panel-blocks and dispatch by label
    for blk in root.select(".panel.movie-panel-info .panel-block"):
        label = _text(blk.select_one("strong"))
        val_container = blk.select_one(".value")
        if not label:
            continue
        if "番號" in label:
            # Prefer code from title, but fallback to here
            if not code and val_container:
                text = _text(val_container)
                m = re.search(r"([A-Za-z0-9]{2,})\s*-\s*(\d{2,})", text)
                if m:
                    code = f"{m.group(1).upper()}-{m.group(2)}"
        elif "日期" in label:
            date = _text(val_container)
        elif "時長" in label or "时长" in label:
            duration_minutes, duration_text = _parse_duration(_text(val_container))
        elif "片商" in label:
            a = val_container.select_one("a") if val_container else None
            maker = {"name": _text(a) or _text(val_container), "href": _safe_href(a)}
        elif "發行" in label or "发行" in label:
            a = val_container.select_one("a") if val_container else None
            publisher = {"name": _text(a) or _text(val_container), "href": _safe_href(a)}
        elif "系列" in label:
            a = val_container.select_one("a") if val_container else None
            series = {"name": _text(a) or _text(val_container), "href": _safe_href(a)}
        elif "評分" in label or "评分" in label:
            rating, rating_count = _parse_rating(_text(val_container))
        elif "類別" in label or "类别" in label:
            for a in (val_container or blk).select("a"):
                categories.append({"name": _text(a), "href": _safe_href(a)})
        elif "演員" in label or "演员" in label:
            # Actors may follow by a <strong class="symbol female/male">
            # We iterate anchors and peek at their next_sibling(s)
            for a in (val_container or blk).select("a"):
                name = _text(a)
                href = _safe_href(a)
                gender = None
                # Check immediate next strong
                nxt = a.next_sibling
                # Walk a couple siblings to tolerate spaces/nbsp
                for _ in range(3):
                    if not nxt:
                        break
                    if getattr(nxt, "name", None) == "strong":
                        cls = (nxt.get("class") or [])
                        if "female" in cls:
                            gender = "female"
                        elif "male" in cls:
                            gender = "male"
                        break
                    nxt = getattr(nxt, "next_sibling", None)
                actors.append({"name": name, "href": href, "gender": gender})

    # Preview screenshots (outside panel, but related)
    screenshots: List[str] = []
    for a in soup.select(".preview-images a.tile-item[href]"):
        href = a.get("href")
        if href:
            screenshots.append(href)

    # Stats: 想看 / 看過 (located near video-detail footer)
    wish_count = watched_count = None
    for el in soup.select(".video-detail .panel-block span.is-size-7"):
        text = _text(el)
        m1 = re.search(r"([0-9,]+)人想看", text)
        if m1:
            try:
                wish_count = int(m1.group(1).replace(",", ""))
            except Exception:
                pass
        m2 = re.search(r"([0-9,]+)人看過", text)
        if m2:
            try:
                watched_count = int(m2.group(1).replace(",", ""))
            except Exception:
                pass

    # Magnets within current HTML (if present)
    magnets = _parse_magnets(soup)

    # Initial related lists if already present in HTML (after dynamic load)
    initial_related_lists = _parse_related_lists_from_soup(soup)

    # Tab URLs (may require ajax to load)
    review_tab_url = _find_tab_url(soup, tab_class="review-tab")
    related_lists_url = _find_tab_url(soup, tab_class="list-tab")

    # Recommendations: 你可能也喜歡
    recommendations = _parse_recommendations(soup)

    detail = VideoDetail(
        id=code,
        code=code,
        title=title,
        canonical_url=canonical_url,
        href_path=href_path,
        cover=cover,
        cover_full=cover_full,
        screenshots=screenshots,
        date=date,
        duration_minutes=duration_minutes,
        duration_text=duration_text,
        maker=maker,
        publisher=publisher,
        series=series,
        categories=categories,
        actors=actors,
        rating=rating,
        rating_count=rating_count,
        stats={"wish": wish_count, "watched": watched_count},
        magnets=magnets,
        reviews=[],
        related_lists=initial_related_lists,
        recommendations=recommendations,
        review_tab_url=review_tab_url,
        related_lists_url=related_lists_url,
    )
    return detail


def parse_file(path: str, *, base_domains: Optional[List[str]] = None) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    detail = parse_video_detail_html(html, base_domains=base_domains)
    return detail.to_dict()


# Note: MovieScraper and execution loop have been moved to script/javdb/movie.py


if __name__ == "__main__":
    # Demo: parse local sample.html and pretty-print JSON
    USEFUL_COOKIE_KEYS = [
    "cf_clearance",      # Cloudflare challenge clearance
    "_jdb_session",      # Site session
    "remember_me_token", # Persistent login
    "over18",            # Adult gate bypass
    "locale",            # Language preference
    "_rucaptcha_session_id", # Captcha session (optional)
    ]

    import argparse

    parser = argparse.ArgumentParser(description="Parse JavDB video detail page to JSON")
    parser.add_argument("file", nargs="?", default=None, help="HTML file path (optional when --url is set)")
    parser.add_argument("--url", dest="url", help="URL of the video detail page", default=None)
    parser.add_argument("--fetch-tabs", action="store_true", help="Fetch reviews and related lists tabs if available")
    parser.add_argument("--cookie", dest="cookie", default=None, help="Cookie header string for authenticated requests")
    parser.add_argument("--cookie-file", dest="cookie_file", default=None, help="Path to a file containing cookies (header string or name\tvalue lines)")
    parser.add_argument(
        "--base",
        nargs="*",
        default=["https://javdb.com", "https://javdb561.com"],
        help="Base domains to resolve relative URLs",
    )
    args = parser.parse_args()

    # Resolve cookie precedence: --cookie > env JAVDB_COOKIE > --cookie-file
    cookie_val = args.cookie
    if not cookie_val:
        env_cookie = os.getenv("JAVDB_COOKIE")
        if env_cookie:
            cookie_val = _parse_cookie_file_or_string(env_cookie, only_keys=USEFUL_COOKIE_KEYS)
    if not cookie_val and args.cookie_file:
        try:
            with open(args.cookie_file, "r", encoding="utf-8") as f:
                raw = f.read()
            cookie_val = _parse_cookie_file_or_string(raw, only_keys=USEFUL_COOKIE_KEYS)
        except Exception:
            cookie_val = None

    if args.url:
        data = parse_url(args.url, base_domains=args.base, fetch_tabs=args.fetch_tabs, cookie=cookie_val)
    else:
        path = args.file or "script/sample.html"
        data = parse_file(path, base_domains=args.base)
    print(json.dumps(data, ensure_ascii=False, indent=2))
