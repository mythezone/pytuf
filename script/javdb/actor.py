from __future__ import annotations

from urllib.parse import urljoin, urlparse
import re
import time
from typing import Dict, List

from base import BaseScraper, MongoDB

base_url = "https://javdb561.com"


class ActorScraper(BaseScraper):
    def __init__(self, actor_href: str):
        super().__init__()
        self.actor_href = actor_href
        # 统一计算绝对 URL 与相对路径，避免写库时键不一致
        self.actor_url = urljoin(base_url, actor_href)
        self.actor_path = urlparse(self.actor_url).path  # 形如 /actors/XXXX
        self.db = MongoDB()
        self.actors_col = "actors"
        self.movies_col = "movies"

    # ---------- helpers ----------
    @staticmethod
    def _text(el) -> str:
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _num_in_text(text: str) -> float:
        m = re.search(r"([0-9]+\.?[0-9]*)", text)
        return float(m.group(1)) if m else 0.0

    @staticmethod
    def _int_in_text(text: str) -> int:
        m = re.search(r"([0-9]+)", text)
        return int(m.group(1)) if m else 0

    def _parse_actor_tags(self) -> List[str]:
        tags = []
        wrap = self.soup.select_one(".actor-tags")
        if not wrap:
            return tags
        for a in wrap.select("a.tag"):
            t = self._text(a)
            if not t or t == "全部":
                continue
            # 去掉括号内的计数，例如 美乳(33) -> 美乳
            t = re.sub(r"\(\d+\)$", "", t).strip()
            if t:
                tags.append(t)
        return tags

    def _parse_movie_items(self) -> List[Dict]:
        results: List[Dict] = []
        grid = self.soup.select("div.item > a.box")
        for a in grid:
            href = a.get("href") or ""
            link = urljoin(base_url, href)
            # 统一存相对路径，避免混用绝对/相对导致的去重/更新不一致
            link_path = urlparse(link).path
            cover_img = a.select_one(".cover img")
            cover = cover_img.get("src") if cover_img else None
            vt = a.select_one(".video-title")
            strong = vt.select_one("strong") if vt else None
            code_id = self._text(strong)
            full_title = self._text(vt)
            # remove code_id from title text
            title = full_title.replace(code_id, "", 1).strip()
            score_val = self._text(a.select_one(".score .value"))
            rating = self._num_in_text(score_val)
            rater = 0
            # e.g. "4.68分, 由160人評價" -> 160
            m = re.search(r"由(\d+)人", score_val)
            if m:
                rater = int(m.group(1))
            date_text = self._text(a.select_one(".meta"))
            tag_texts = [self._text(t) for t in a.select(".tags .tag")]

            # minimal info for actor.movie_list
            min_info = {
                "title": title,
                "href": link_path,
                "cover": cover,
                "id": code_id,
            }
            # detailed movie doc
            movie_doc = {
                "title": title,
                "code": code_id,
                "href": link_path,
                "cover": cover,
                "rating": rating,
                "rater": rater,
                "publish_date": date_text,
                "tags": [t for t in tag_texts if t],
                "source": "javdb",
            }
            results.append({"min": min_info, "doc": movie_doc})
        return results

    def _next_page(self) -> str | None:
        nxt = self.soup.select_one(".pagination a.pagination-next[rel='next']")
        if nxt and nxt.get("href"):
            return urljoin(base_url, nxt.get("href"))
        return None

    def _parse_total_count(self) -> int | None:
        # example: <span class="section-meta">46 部影片</span>
        meta = self.soup.select_one(".section-meta")
        if not meta:
            return None
        m = re.search(r"(\d+)\s*部", meta.get_text(strip=True))
        return int(m.group(1)) if m else None

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        s = int(max(0, seconds))
        d, s = divmod(s, 86400)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        out = []
        if d:
            out.append(f"{d}d")
        if h or d:
            out.append(f"{h}h")
        if m or h or d:
            out.append(f"{m}m")
        out.append(f"{s}s")
        return " ".join(out)

    def _draw_progress(self, processed: int, total: int, start_ts: float) -> None:
        import sys, time as _t

        elapsed = _t.time() - start_ts
        sp_item = (elapsed / processed) if processed > 0 else 0
        remain = max(0, total - processed)
        eta = sp_item * remain
        # bar
        width = 30
        ratio = (processed / total) if total > 0 else 0
        filled = int(width * ratio)
        bar = "█" * filled + "─" * (width - filled)
        percent = ratio * 100.0
        line = f"[{bar}] {processed}/{total} ({percent:.1f}%) | {sp_item:.2f}s/item | ETA {self._fmt_duration(eta)}"
        sys.stdout.write("\r" + line)
        sys.stdout.flush()

    # ---------- normalization & merging ----------
    def _merge_values(self, a, b):
        return b if (a is None or a == "" or a == []) else a

    def _merge_lists(self, a_list, b_list):
        if not isinstance(a_list, list):
            return b_list if isinstance(b_list, list) else a_list
        if not isinstance(b_list, list):
            return a_list

        def key_of(x):
            if isinstance(x, dict):
                return x.get("href") or x.get("id") or repr(sorted(x.items()))
            return x

        seen = set()
        out = []
        for src in (a_list, b_list):
            for it in src:
                k = key_of(it)
                if k in seen:
                    continue
                seen.add(k)
                out.append(it)
        return out

    def _merge_docs(self, target: dict, source: dict) -> dict:
        merged = dict(target)
        for k, v in source.items():
            if k == "_id":
                continue
            tv = merged.get(k)
            if isinstance(tv, list) or isinstance(v, list):
                merged[k] = self._merge_lists(
                    tv if isinstance(tv, list) else [], v if isinstance(v, list) else []
                )
            elif isinstance(tv, dict) and isinstance(v, dict):
                mv = dict(tv)
                for kk, vv in v.items():
                    if kk == "_id":
                        continue
                    mv[kk] = self._merge_values(mv.get(kk), vv)
                merged[k] = mv
            else:
                merged[k] = self._merge_values(tv, v)
        return merged

    def _normalize_href_in_collection(self, collection: str, path: str) -> None:
        col = self.db.db[collection]
        rel = col.find_one({"href": path})
        abs_doc = col.find_one(
            {"href": {"$regex": f"^https?://[^/]+{re.escape(path)}$"}}
        )
        if abs_doc and not rel:
            col.update_one({"_id": abs_doc["_id"]}, {"$set": {"href": path}})
            return
        if abs_doc and rel and abs_doc["_id"] != rel["_id"]:
            merged = self._merge_docs(rel, abs_doc)
            col.update_one({"_id": rel["_id"]}, {"$set": merged})
            col.delete_one({"_id": abs_doc["_id"]})

    # ---------- main ----------
    def run(self) -> dict:
        # 初始化第一页
        self.init(self.actor_url)
        if not self.soup:
            return {"inserted": 0, "updated": 0}

        # actor 基本与标签
        tags = self._parse_actor_tags()

        # 累计 movie 列表（用于写回 actor 文档）
        actor_movie_list: List[Dict] = []
        inserted = 0
        updated = 0

        current_url = self.actor_url
        total_count = self._parse_total_count() or 0
        processed_count = 0
        import time as _t

        start_ts = _t.time()
        while True:
            # 解析当页电影卡片
            items = self._parse_movie_items()
            for it in items:
                doc = it["doc"]
                href = doc["href"]  # 已经是相对路径
                # 规范库内 href 并合并可能存在的绝对链接文档
                self._normalize_href_in_collection(self.movies_col, href)
                # upsert 到 movies 集合（以 href 作为唯一键）
                res = self.db.db[self.movies_col].update_one(
                    {"href": href}, {"$set": doc}, upsert=True
                )
                if res.upserted_id:
                    movie_id = str(res.upserted_id)
                    inserted += 1
                else:
                    # 已存在则取现有 _id
                    existing = self.db.db[self.movies_col].find_one(
                        {"href": href}, {"_id": 1}
                    )
                    movie_id = str(existing["_id"]) if existing else None
                    updated += 1

                min_info = it["min"].copy()
                if movie_id:
                    min_info["mongo_id"] = movie_id
                actor_movie_list.append(min_info)

            # 翻页
            processed_count += len(items)
            if total_count:
                self._draw_progress(processed_count, total_count, start_ts)
            next_url = self._next_page()
            if not next_url:
                break
            current_url = next_url
            self.init(current_url)
            time.sleep(2)

        if total_count:
            import sys

            sys.stdout.write("\n")
            sys.stdout.flush()

        # 更新前：规范演员文档，清理可能存在的绝对/相对重复
        self._normalize_href_in_collection(self.actors_col, self.actor_path)
        # 更新 actor 文档：兼容 href 为绝对/相对，或使用 link 字段的历史数据
        actor_filter = {
            "$or": [
                {"href": self.actor_href},
                {"href": self.actor_path},
                {"link": self.actor_href},
                {"link": self.actor_path},
            ]
        }
        update_doc = {
            "$set": {
                "tags": tags,
                "movie_list": actor_movie_list,
                "href": self.actor_path,
            }
        }
        res_actor = self.db.db[self.actors_col].update_one(
            actor_filter, update_doc, upsert=True
        )
        if res_actor.upserted_id:
            print(f"[ActorScraper] 新增演员文档: {self.actor_path}")

        return {
            "inserted": inserted,
            "updated": updated,
            "movies": len(actor_movie_list),
        }


if __name__ == "__main__":
    """
    从 actors 集合中取出一个未处理的演员（movie_list_parsed != True），
    执行抓取与写库，并将该演员标记为已处理。每轮间隔 20 秒。
    """
    from pymongo import ASCENDING
    from datetime import datetime, timezone

    db = MongoDB()
    actors = db.db["actors"]

    # 测试单个
    # doc = actors.find_one({"href": "/actors/Av2e"})
    # print(doc)

    import sys as _sys

    def wait_progress(seconds: int, label: str = "wait") -> None:
        width = 30
        start = time.time()
        while True:
            el = time.time() - start
            if el > seconds:
                el = seconds
            ratio = el / seconds if seconds > 0 else 1
            filled = int(width * ratio)
            bar = "█" * filled + "─" * (width - filled)
            pct = ratio * 100
            remaining = max(0, int(seconds - el))
            _sys.stdout.write("\r" + f"[{bar}] {pct:5.1f}% | {label} {remaining:2d}s")
            _sys.stdout.flush()
            if el >= seconds:
                break
            time.sleep(0.1)
        _sys.stdout.write("\r" + " " * 80 + "\r")
        _sys.stdout.flush()

    # 批量处理
    while True:
        doc = actors.find_one(
            {"movie_list_parsed": {"$ne": True}, "href": {"$exists": True}},
            sort=[("_id", ASCENDING)],
        )
        if not doc:
            wait_progress(20, label="idle")
            continue

        href = doc.get("href")
        print(f"[ActorScraper] 处理演员: {href}")
        try:
            scraper = ActorScraper(href)
            stats = scraper.run()
            # 标记处理完成
            actors.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "movie_list_parsed": True,
                        "movie_list_parsed_at": datetime.now(timezone.utc),
                        "last_stats": stats,
                    }
                },
            )
            print(f"[ActorScraper] 完成: {href} -> {stats}")
        except Exception as e:
            # 发生异常时记录错误，避免死循环卡住同一条
            actors.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "movie_list_error": str(e),
                        "movie_list_parsed": False,
                        "movie_list_error_at": datetime.now(timezone.utc),
                    }
                },
            )
            print(f"[ActorScraper] 处理失败: {href} -> {e}")

        # 间隔 20s 再处理下一条（显示等待进度条）
        wait_progress(30, label="cooldown")

    # 单次处理测试
    # doc = actors.find_one(
    #     {"movie_list_parsed": {"$ne": True}, "href": {"$exists": True}}
    # )
    # doc = actors.find_one({"href": "/actors/00z7"})

    # if doc:
    #     href = doc.get("href")
    #     print(f"[ActorScraper] 处理演员: {href}")
    #     try:
    #         scraper = ActorScraper(href)
    #         stats = scraper.run()
    #         # 标记处理完成
    #         actors.update_one(
    #             {"_id": doc["_id"]},
    #             {
    #                 "$set": {
    #                     "movie_list_parsed": True,
    #                     "movie_list_parsed_at": datetime.now(timezone.utc),
    #                     "last_stats": stats,
    #                 }
    #             },
    #         )
    #         print(f"[ActorScraper] 完成: {href} -> {stats}")
    #     except Exception as e:
    #         # 发生异常时记录错误，避免死循环卡住同一条
    #         actors.update_one(
    #             {"_id": doc["_id"]},
    #             {
    #                 "$set": {
    #                     "movie_list_error": str(e),
    #                     "movie_list_parsed": False,
    #                     "movie_list_error_at": datetime.now(timezone.utc),
    #                 }
    #             },
    #         )
    #         print(f"[ActorScraper] 处理失败: {href} -> {e}")
