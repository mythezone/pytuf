import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin
from pprint import pprint
import hashlib
import os
from typing import Callable, Dict, List, Optional, Any

mongo_url = "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
db_name = "myj"


def save_to_mongo(data_list, collection_name, key="", mongo_url=mongo_url, db_name=db_name):
    """
    将一个 dict 保存到 MongoDB。
    :param data_dict: 待保存的字典
    :param key: 用于去重的字段
    :param mongo_url: MongoDB 连接 URL，形如 mongodb://localhost:27017/
    :param db_name: 数据库名称
    :param collection_name: 主集合名称 (存储业务文档)
    :return: 插入后的文档 _id
    """
    # 连接 MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]
    
    if key!="":
        # 去重
        for data in data_list:
            if collection.find_one({key: data[key]}):
                print(f"已存在 {key} 为 {data[key]} 的数据，跳过")
                continue
            
            # 将 dict 插入 MongoDB，返回 _id
            inserted_id = collection.insert_one(data).inserted_id
            print(f"已插入 MongoDB 文档到 {collection_name}，_id: {inserted_id}")
        print(f"已插入 {len(data_list)} 条数据到 {collection_name}")
    else:
        inserted_ids = collection.insert_many(data_list)
        print(f"已插入 {len(inserted_ids.inserted_ids)} 条数据到 {collection_name}")


def get_list(url, item_selector, next_selector, parser=None, save = True, key ="", collection_name = "test_collection"):
    """
    爬取列表页面，支持自动翻页。
    :param url: 起始页面 URL
    :param item_selector: 列表项的选择器字符串
    :param next_selector: 下一页的选择器字符串
    :param parser: 可选的解析器函数。如果为 None，则直接返回找到的元素列表；
                   否则对每个元素调用 parser(item) 并将解析结果加入返回列表。
    :return: 符合条件的列表项（原始的元素或经 parser 处理后的结果）的列表
    """
    results = []
    current_url = url
    count = 0
    while True:
        count+=1
        print(f"GetList in 第{count}页: {current_url}")
        resp = requests.get(current_url, timeout=10)
        if not resp.ok:
            print(f"请求失败，状态码: {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 获取列表项
        items = soup.select(item_selector)
        if parser is None:
            # 不使用解析器，直接返回元素
            results.extend(items)
        else:
            # 使用用户自定义解析器对每个 item 进行处理
            for item in items:
                parsed_data = parser(item)
                results.append(parsed_data)
                
        pprint(results)
        if save:
            save_to_mongo(results, collection_name=collection_name,key=key) 
            results = []

        # 找到“下一页”链接并更新 current_url，如果没有则终止循环
        next_page = soup.select_one(next_selector)
        if not next_page:
            # 没有下一页时，结束
            break

        next_href = next_page.get('href')
        if not next_href:
            # 如果下一页链接没有 href 属性，也结束
            break
        # 处理相对路径
        current_url = next_href #urljoin(current_url, next_href)
        

    return results


def parse_detail(url, parse_dict, additional_dict={}):
    """
    解析详情页并将结果插入到 MongoDB。
    :param url: 需要解析的详情页 URL
    :param parse_dict: dict, 形如 { "字段名": "对应的选择器字符串", ... }
    :param additional_dict: dict, 需要附加到解析结果中的其它信息
    """


    resp = requests.get(url, timeout=10)
    if not resp.ok:
        print(f"请求失败，状态码: {resp.status_code}")
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 解析页面内容
    result = {}
    for field_key, (field_selector, field_type) in parse_dict.items():
        if "list" in field_type:
            element = soup.select(field_selector)
        else:
            element = soup.select_one(field_selector)
            
        if element:
            # 获取文本并去除首尾空白
            if  field_type == "href":
                result[field_key] = element.get("href")
            elif field_type == "src":
                result[field_key] = element.get("src")
            elif field_type == "data-src":
                result[field_key] = element.get("data-src")
            elif field_type == "html":
                result[field_key] = element.prettify()
            elif field_type == "list-href":
                result[field_key] = [item.get("href") for item in element]
            elif field_type == "list-src":
                tmp = []
                for item in element:
                    t_src = item.get('src')
                    if t_src:
                        tmp.append(t_src)
                    else:
                        tmp.append(item.get("data-src"))
                result[field_key] = tmp 
            elif field_type == "list-text":
                result[field_key] = [item.get_text(strip=True) for item in element]
            elif field_type == "list-data-src":
                result[field_key] = [item.get("data-src") for item in element]
            else:
                result[field_key] = element.get_text(strip=True)
        else:
            # 没匹配到对应元素，设置为 None 或者空字符串等
            result[field_key] = None

    # 将额外信息合并进结果
    if additional_dict:
        result.update(additional_dict)

    return result

class ImageDownloadError(Exception):
    """自定义异常：网络相关的图片下载失败时抛出"""
    def __init__(self, doc_code, url, error):
        self.doc_code = doc_code
        self.url = url
        self.error = error
        self.message = f"下载图片失败: {url} - 错误: {error}"
        super().__init__(self.message)

def download_image(session, url, doc_code, index, type_="movie"):
    """
    下载单个图片，并返回新的 URL。

    :param session: requests.Session 对象
    :param url: 图片 URL
    :param doc_code: 文档代码，用于命名
    :param index: 图片索引
    :param save_folder: 保存根目录
    :return: 新的 URL（hash:filename）或 None
    :raises ImageDownloadError: 如果遇到网络相关的下载错误
    """
    if type_ == "movie":
        save_folder = r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\movie"
    else:
        save_folder = r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\actress"
        
        
    if not url.startswith("http"):
        print(f"非 HTTP URL，跳过: {url}")
        return None
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        image = response.content
    except requests.exceptions.SSLError as e:
        raise ImageDownloadError(doc_code, url, e)
    except requests.exceptions.ConnectionError as e:
        raise ImageDownloadError(doc_code, url, e)
    except requests.exceptions.Timeout as e:
        raise ImageDownloadError(doc_code, url, e)
    except requests.exceptions.RequestException as e:
        raise ImageDownloadError(doc_code, url, e)

    # 处理图片保存
    try:
        # 提取文件扩展名，处理可能的查询参数
        extend_name = url.split(".")[-1].split('?')[0]
        # 如果扩展名过长或不存在，默认使用 jpg
        if len(extend_name) > 5 or not extend_name.isalnum():
            extend_name = "jpg"
        image_name = f"{doc_code}_{index}.{extend_name}"

        # 计算 MD5 哈希值
        image_hash = hashlib.md5(image).hexdigest()

        # 使用哈希值的前四个字符创建两层文件夹
        if type_ == "movie":
            folder = os.path.join(save_folder, image_hash[:2], image_hash[2:4])
        else:
            folder = os.path.join(save_folder, image_hash[0])
        os.makedirs(folder, exist_ok=True)

        # 保存图片到本地
        image_path = os.path.join(folder, image_name)
        with open(image_path, "wb") as f:
            f.write(image)

        # 返回新的 URL（格式为 hash:filename）
        return f"{image_hash}:{image_name}"
    
    except Exception as e:
        print(f"保存图片失败: {url} - 错误: {e}")
        return None  # 保存失败，返回 None 但不抛出异常


class PublisherCrawler:
    """
    通用发行商爬虫：通过初始化参数适配不同站点/发行商，支持增量爬取。

    最低依赖：
    - 站点的演员列表选择器与解析函数（或统一结构）
    - 演员详情页解析字典（parse_dict）
    - 演员详情页中的影片列表选择器（用于获取演员下的影片链接）
    - 影片详情页解析字典（parse_dict）
    - 影片 code 提取函数（从详情 URL 提取 code，用于去重）

    Mongo 约定：
    - 演员集合：默认 "actress"，字段包含 publisher/link/…/movies 等
    - 影片集合：默认 "movie"，以 code 去重

    增量规则：
    - 演员列表：以 link 去重插入
    - 演员详情：查找 detail_parsed != True 的记录更新
    - 演员电影列表：合并新链接到 doc.movies（按 link 去重）
    - 影片详情：对 doc.movies[] 中 parsed != True 的逐个解析/入库，写回 id/parsed
    - 图片下载：对 image_parsed != True 的影片/演员处理
    """

    def __init__(
        self,
        *,
        publisher: str,
        actor_index_urls: List[str],
        actor_item_selector: str,
        actor_next_selector: str,
        actor_item_parser: Callable[[Any], Dict[str, Any]],
        actor_detail_parse: Dict[str, List[str]],
        actor_detail_additional: Optional[Dict[str, Any]] = None,
        actor_movies_item_selector: Optional[str] = None,
        actor_movies_next_selector: Optional[str] = None,
        actor_movies_item_parser: Optional[Callable[[Any], Dict[str, Any]]] = None,
        movie_detail_parse: Optional[Dict[str, List[str]]] = None,
        movie_code_extractor: Optional[Callable[[str], str]] = None,
        mongo_url_: str = mongo_url,
        db_name_: str = db_name,
        actress_collection_name: str = "actress",
        movie_collection_name: str = "movie",
    ) -> None:
        self.publisher = publisher
        self.actor_index_urls = actor_index_urls
        self.actor_item_selector = actor_item_selector
        self.actor_next_selector = actor_next_selector
        self.actor_item_parser = actor_item_parser
        self.actor_detail_parse = actor_detail_parse
        self.actor_detail_additional = actor_detail_additional or {"detail_parsed": True}
        self.actor_movies_item_selector = actor_movies_item_selector
        self.actor_movies_next_selector = actor_movies_next_selector
        self.actor_movies_item_parser = actor_movies_item_parser
        self.movie_detail_parse = movie_detail_parse
        self.movie_code_extractor = movie_code_extractor

        # DB handles
        client = MongoClient(mongo_url_)
        db = client[db_name_]
        self._actress_col = db[actress_collection_name]
        self._movie_col = db[movie_collection_name]

    # ---------- 基础持久化 ----------
    def _upsert_many_by_key(self, docs: List[Dict], collection, key: str) -> int:
        """按 key 去重插入；存在则跳过，返回新增数量。"""
        inserted = 0
        for d in docs:
            if not d:
                continue
            if key and collection.find_one({key: d.get(key)}):
                continue
            collection.insert_one(d)
            inserted += 1
        return inserted

    # ---------- 演员列表 ----------
    def crawl_actor_index(self, incremental: bool = True) -> int:
        """爬取演员索引列表；若 incremental=True 则以 link 去重。返回新增条数。"""
        total_new = 0
        for url in self.actor_index_urls:
            results = get_list(
                url=url,
                item_selector=self.actor_item_selector,
                next_selector=self.actor_next_selector,
                parser=self.actor_item_parser,
                save=False,
            )
            # 强制写入 publisher 字段，防止 parser 遗漏
            for r in results:
                if r is not None:
                    r.setdefault("publisher", self.publisher)
            if incremental:
                total_new += self._upsert_many_by_key(results, self._actress_col, key="link")
            else:
                save_to_mongo(results, collection_name=self._actress_col.name, key="link")
                total_new += len(results)
        return total_new

    # ---------- 演员详情 + 影片列表 ----------
    def _fetch_actor_movies(self, actor_detail_url: str) -> List[Dict[str, Any]]:
        if not (self.actor_movies_item_selector and self.actor_movies_next_selector and self.actor_movies_item_parser):
            return []
        return get_list(
            url=actor_detail_url,
            item_selector=self.actor_movies_item_selector,
            next_selector=self.actor_movies_next_selector,
            parser=self.actor_movies_item_parser,
            save=False,
        )

    def update_actor_details(self, selector: Optional[Dict] = None, sleep_time: float = 0) -> int:
        """解析演员详情（增量：detail_parsed != True）。返回更新数量。"""
        import time as _time
        q = {"publisher": self.publisher, "detail_parsed": {"$ne": True}}
        if selector:
            q.update(selector)
        updated = 0
        for doc in self._actress_col.find(q):
            detail_url = doc.get("link")
            if not detail_url:
                continue
            detail_result = parse_detail(
                url=detail_url,
                parse_dict=self.actor_detail_parse,
                additional_dict=self.actor_detail_additional,
            ) or {}
            # 影片列表（增量合并）
            movies = self._fetch_actor_movies(detail_url)
            if movies:
                old_movies = doc.get("movies", [])
                known = {m.get("link") for m in old_movies if m and m.get("link")}
                for m in movies:
                    if m and m.get("link") not in known:
                        old_movies.append(m)
                detail_result["movies"] = old_movies

            if detail_result:
                self._actress_col.update_one({"_id": doc["_id"]}, {"$set": detail_result})
                updated += 1
            if sleep_time:
                _time.sleep(sleep_time)
        return updated

    def refresh_actor_movies(self) -> int:
        """仅刷新演员的 movies 列表（不改 detail 其它字段）。返回更新数量。"""
        updated = 0
        for doc in self._actress_col.find({"publisher": self.publisher}):
            detail_url = doc.get("link")
            if not detail_url:
                continue
            movies = self._fetch_actor_movies(detail_url)
            if not movies:
                continue
            old_movies = doc.get("movies", [])
            known = {m.get("link") for m in old_movies if m and m.get("link")}
            changed = False
            for m in movies:
                if m and m.get("link") not in known:
                    old_movies.append(m)
                    changed = True
            if changed:
                self._actress_col.update_one({"_id": doc["_id"]}, {"$set": {"movies": old_movies}})
                updated += 1
        return updated

    # ---------- 影片详情 ----------
    def _movie_exists(self, code: str) -> Optional[str]:
        doc = self._movie_col.find_one({"code": code})
        if doc:
            return str(doc["_id"])
        return None

    def _parse_movie_detail(self, url: str) -> Optional[Dict[str, Any]]:
        if not (self.movie_detail_parse and self.movie_code_extractor):
            return None
        code = self.movie_code_extractor(url)
        addition = {"code": code, "publisher": self.publisher, "link": url}
        detail = parse_detail(url=url, parse_dict=self.movie_detail_parse, additional_dict=addition)
        return detail

    def update_movies(self, limit_per_actor: Optional[int] = None) -> int:
        """
        解析并写入影片详情（增量：对 actor.movies 中 parsed != True 的条目）。
        返回本次成功写入/关联的影片数量。
        """
        total = 0
        for doc in self._actress_col.find({"publisher": self.publisher}):
            movies = doc.get("movies", [])
            changed = False
            handled = 0
            for m in movies:
                if limit_per_actor is not None and handled >= limit_per_actor:
                    break
                if not m or m.get("parsed"):
                    continue
                link = m.get("link")
                if not link:
                    continue
                code = self.movie_code_extractor(link) if self.movie_code_extractor else None
                existed_id = self._movie_exists(code) if code else None
                if existed_id:
                    m["id"] = existed_id
                    m["parsed"] = True
                    changed = True
                    handled += 1
                    total += 1
                    continue
                detail = self._parse_movie_detail(link)
                if detail:
                    inserted_id = self._movie_col.insert_one(detail).inserted_id
                    m["id"] = str(inserted_id)
                    m["parsed"] = True
                    changed = True
                    handled += 1
                    total += 1
            if changed:
                # 若全部解析完成，可标注 movies_parsed=True（可选）
                all_done = all(bool(m.get("parsed")) for m in movies if m)
                patch = {"movies": movies}
                if all_done:
                    patch["movies_parsed"] = True
                self._actress_col.update_one({"_id": doc["_id"]}, {"$set": patch})
        return total

    # ---------- 图片下载 ----------
    def download_movie_images(
        self,
        *,
        save_folder: str,
        max_workers: int = 5,
    ) -> int:
        """为当前发行商下载影片 screenshots，并替换为本地哈希路径。返回处理文档数。"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        processed = 0
        collection = self._movie_col
        with requests.Session() as session, ThreadPoolExecutor(max_workers=max_workers) as executor:
            for doc in collection.find({"publisher": self.publisher, "image_parsed": {"$ne": True}}):
                screenshots = doc.get("screenshots", [])
                if not screenshots:
                    continue
                futures = {}
                for i, url in enumerate(screenshots):
                    if isinstance(url, str) and url.startswith("http"):
                        futures[executor.submit(download_image, session, url, doc.get("code", "unknown"), i, "movie")] = i
                    else:
                        screenshots[i] = None
                for fut in as_completed(futures):
                    i = futures[fut]
                    try:
                        new_url = fut.result()
                        screenshots[i] = new_url if new_url else None
                    except Exception as e:
                        print(f"下载图片异常: {e}")
                        screenshots[i] = None
                patch = {"screenshots": screenshots, "image_parsed": True}
                collection.update_one({"_id": doc["_id"]}, {"$set": patch})
                processed += 1
        return processed

    def download_actress_avatars(self, *, save_folder: str) -> int:
        """为当前发行商下载演员头像并替换链接。返回处理文档数。"""
        processed = 0
        for doc in self._actress_col.find({"publisher": self.publisher, "image_parsed": {"$ne": True}}):
            url = doc.get("avatar")
            if not url or not isinstance(url, str) or not url.startswith("http"):
                continue
            try:
                resp = requests.get(url, timeout=10)
                if not resp.ok:
                    continue
                image = resp.content
                extend_name = url.split(".")[-1].split('?')[0]
                if len(extend_name) > 5 or not extend_name.isalnum():
                    extend_name = "jpg"
                image_name = f"{doc.get('japan_name','unknown')}.{extend_name}"
                image_hash = hashlib.md5(image).hexdigest()
                folder = os.path.join(save_folder, image_hash[0])
                os.makedirs(folder, exist_ok=True)
                image_path = os.path.join(folder, image_name)
                with open(image_path, "wb") as f:
                    f.write(image)
                self._actress_col.update_one({"_id": doc["_id"]}, {"$set": {"avatar": image_path, "image_parsed": True}})
                processed += 1
            except Exception as e:
                print(f"下载头像失败: {e}")
        return processed

    # ---------- 一键增量 ----------
    def incremental_run(
        self,
        *,
        crawl_index: bool = True,
        update_details: bool = True,
        refresh_movies: bool = True,
        update_movies: bool = True,
        download_images: bool = False,
        movie_image_folder: Optional[str] = None,
        avatar_folder: Optional[str] = None,
    ) -> Dict[str, int]:
        """一键按需增量执行各阶段，返回各阶段计数。"""
        stats = {}
        if crawl_index:
            stats["actor_index_new"] = self.crawl_actor_index(incremental=True)
        if update_details:
            stats["actor_details_updated"] = self.update_actor_details()
        if refresh_movies:
            stats["actor_movies_refreshed"] = self.refresh_actor_movies()
        if update_movies:
            stats["movies_updated"] = self.update_movies()
        if download_images and movie_image_folder:
            stats["movie_images_downloaded"] = self.download_movie_images(save_folder=movie_image_folder)
        if download_images and avatar_folder:
            stats["avatars_downloaded"] = self.download_actress_avatars(save_folder=avatar_folder)
        return stats
