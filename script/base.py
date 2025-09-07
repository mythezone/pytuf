from __future__ import annotations
import time
import requests
import random
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import json
import os
from pathlib import Path
from pprint import pprint
from typing import List, Dict, Optional

from pymongo import MongoClient
from pymongo import UpdateOne
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BaseScraper:

    def __init__(
        self,
        cookies_file: str | None = None,
    ):
        self.session = requests.Session()
        # headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }
        # load cookies.txt into Cookie header
        cookie_header = self._load_cookie_header(cookies_file)
        if cookie_header:
            headers["Cookie"] = cookie_header
        self.session.headers.update(headers)

        # mount retries for transient network/SSL issues
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("HEAD", "GET", "OPTIONS"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.soup: Optional[bs] = None
        self.last_error: Optional[Exception] = None

    def _load_cookie_header(self, cookies_file: str) -> Optional[str]:
        """
        读取 cookies 文件并返回可直接用于 HTTP Header 的 Cookie 字符串。
        支持以下格式：
        - 单行原始 Header（可带或不带前缀 'Cookie:'）
        - 多行 "key=value" 列表（将自动以 "; " 连接）
        - JSON 对象 {"k":"v", ...}
        """

        if not cookies_file:
            return None
        try:
            with open(cookies_file, "r", encoding="utf-8") as f:
                raw = f.read().strip()
        except FileNotFoundError:
            return None

        if not raw:
            return None

        # Case 1: JSON dict
        if raw.startswith("{") and raw.endswith("}"):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    parts = [f"{k}={v}" for k, v in data.items()]
                    return "; ".join(parts)
            except Exception:
                pass

        # Case 2: starts with 'Cookie:'
        if raw.lower().startswith("cookie:"):
            return raw.split(":", 1)[1].strip()

        # Case 3: multi-line key=value
        if "\n" in raw:
            parts = []
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line and line.lower().startswith("cookie:"):
                    # allow embedded header lines
                    line = line.split(":", 1)[1].strip()
                parts.extend([p.strip() for p in line.split(";") if p.strip()])
            return "; ".join(parts) if parts else None

        # Case 4: single line already formatted
        return raw

    def init(self, url: str):
        self.url = url
        self._get_whole_html()

    def _cookie_header(self, cookie: Optional[str]) -> Optional[str]:
        if not cookie:
            return None
        if cookie.lower().startswith("cookie:"):
            return cookie.split(":", 1)[1].strip()
        return cookie

    def _get_whole_html(self):
        self.last_error = None
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            self.soup = bs(response.text, "html.parser")
            return
        except requests.exceptions.SSLError as e:
            self.last_error = e
            # Fallback once with verify=False (only if absolutely necessary)
            try:
                response = self.session.get(self.url, timeout=10, verify=False)
                response.raise_for_status()
                self.soup = bs(response.text, "html.parser")
                return
            except Exception as e2:
                self.last_error = e2
                print(f"SSL error fetching {self.url}: {e}")
        except requests.RequestException as e:
            self.last_error = e
            print(f"Failed to retrieve page: {self.url} with error: {e}")
        # failure
        self.soup = None

    def fetch_unique_elements(self, selector: str):
        if not self.soup:
            return {}

        elements = self.soup.select(selector)
        # unique_elements = list({str(el): el for el in elements}.values())
        # return unique_elements
        return elements

    def get_list(self, soup: bs, selector: str) -> List[str]:
        elements = soup.select(selector)
        return elements

    def get_dict(self, soup: bs, dct: Dict[str, str]):
        res = {}
        for key, value in dct.items():
            if key == "text":
                for k, v in value.items():
                    el = soup.select_one(v)
                    res[k] = el.get_text(strip=True) if el else None
            elif key == "href":
                for k, v in value.items():
                    el = soup.select_one(v)
                    href = el["href"] if el and "href" in el.attrs else None
                    # if href and not href.startswith("http"):
                    #     href = urljoin(self.url, href)
                    res[k] = href
            elif key == "src":
                for k, v in value.items():
                    el = soup.select_one(v)
                    src = el["src"] if el and "src" in el.attrs else None
                    # if src and not src.startswith("http"):
                    #     src = urljoin(self.url, src)
                    res[k] = src
            elif key == "title":
                for k, v in value.items():
                    el = soup.select_one(v)
                    title = el["title"] if el and "title" in el.attrs else None
                    res[k] = title
            else:
                print(f"Unknown key: {key}, we will complement it later.")
                continue
        return res

    def save_res(self, res: List[dict], filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename}")


mongo_url = "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
db_name = "jdb"
collection_name = "actors"


class MongoDB:
    def __init__(self, uri=mongo_url, db_name=db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def insert_one(self, collection_name: str, document: dict):
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return result.inserted_id

    def insert_many(
        self,
        collection_name: str,
        documents: List[dict],
        key: str | None = None,
        update_on_duplicate: bool = True,
    ):
        """
        批量写入：
        - 若提供唯一键 key（例如 'href'/'link'/'code'），则对每条记录执行 upsert：
          - 已存在：update（当 update_on_duplicate=True）或跳过（False）
          - 不存在：insert
        - 未提供 key：退化为 insert_many（ordered=False）。

        返回：新插入文档的 _id 列表（更新的文档不返回 id）。
        """
        collection = self.db[collection_name]

        # 自动猜测常见唯一键
        def guess_key(doc: dict) -> str | None:
            if key:
                return key if doc.get(key) is not None else None
            for cand in ("_id", "href", "link", "code"):
                if doc.get(cand) is not None:
                    return cand
            return None

        # 构建批量 upsert 操作
        ops: list[UpdateOne] = []
        fallback_inserts: list[dict] = []
        for d in documents:
            k = guess_key(d)
            if k is None:
                # 无法确定唯一键，走普通插入
                fallback_inserts.append(d)
                continue
            flt = {k: d[k]}
            if update_on_duplicate:
                # 覆盖式更新（仅 set 传入字段）
                ops.append(UpdateOne(flt, {"$set": d}, upsert=True))
            else:
                # 仅在不存在时插入
                ops.append(UpdateOne(flt, {"$setOnInsert": d}, upsert=True))

        inserted_ids: list = []

        if ops:
            res = collection.bulk_write(ops, ordered=False)
            # 仅能拿到 upsert 的新插入 _id，更新的没有 id 返回
            if getattr(res, "upserted_ids", None):
                # upserted_ids 为 {bulk_index: _id}
                inserted_ids.extend(list(res.upserted_ids.values()))

        if fallback_inserts:
            res2 = collection.insert_many(fallback_inserts, ordered=False)
            inserted_ids.extend(res2.inserted_ids)

        return inserted_ids

    def find(self, collection_name: str, query: dict = {}, limit: int = 0):
        collection = self.db[collection_name]
        results = collection.find(query).limit(limit)
        return list(results)

    def update_one(self, collection_name: str, query: dict, update: dict):
        collection = self.db[collection_name]
        result = collection.update_one(query, {"$set": update})
        return result.modified_count

    def delete_one(self, collection_name: str, query: dict):
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count

    def update_many_add_fields(
        self,
        collection_name: str,
        find_query: dict,
        content: dict,
        *,
        upsert: bool = False,
    ) -> dict:
        """
        为满足条件的所有文档批量添加(或覆盖)指定字段内容。

        等价于：db.collection.update_many(find_query, {"$set": content}, upsert=upsert)

        参数:
        - collection_name: 集合名
        - find_query: 查找条件（例：{"publisher": "s1s1s1"}）
        - content: 需要添加/覆盖的字段字典（例：{"source": "crawler"}）
        - upsert: 若无匹配文档是否插入一条（默认 False）

        返回: {"matched": int, "modified": int, "upserted_id": ObjectId|None}
        """
        if not isinstance(find_query, dict) or not isinstance(content, dict):
            raise ValueError("find_query 与 content 必须是 dict")
        collection = self.db[collection_name]
        result = collection.update_many(find_query, {"$set": content}, upsert=upsert)
        return {
            "matched": result.matched_count,
            "modified": result.modified_count,
            "upserted_id": getattr(result, "upserted_id", None),
        }


def page_generator(base_url, location, start=1, end=5):
    for i in range(start, end + 1):
        yield urljoin(base_url, f"{location}?page={i}")


if __name__ == "__main__":
    d = {
        "text": {"name": "strong"},
        "href": {
            "href": "div.actor-box > a",
        },
        "src": {"avatar": "img.avatar"},
        "title": {"title": "div.actor-box > a"},
    }
    scraper = BaseScraper()
    db = MongoDB()

    pages = page_generator("https://javdb561.com", "/actors/western", 1, 30)
    for page in pages:
        scraper.init(page)
        actors_list = scraper.get_list(scraper.soup, "div.actor-box")
        res = []
        for actor in actors_list:
            actor_info = scraper.get_dict(actor, d)
            actor_info["category"] = "uncensored"
            res.append(actor_info)

        # 以 href 作为唯一键，已存在则更新；不存在则插入
        resp = db.insert_many(
            collection_name, res, key="href", update_on_duplicate=True
        )
        print(f"Inserted {len(resp)} documents from {page}")
        time.sleep(random.randint(1, 4))

    # db.update_many_add_fields(
    #     collection_name,
    #     {},
    #     {"category": "censored"},
    #     upsert=False,
    # )
