from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from clawer import *
import time 
from change_proxy import *

names = ['a','ka','sa','ta','na','ha','ma','ya','ra','wa']
actor_url = "https://mvg.jp/actress/"
actor_selector = "div.p-hoverCard"
actor_next_selector = "a[rel='next']"

movie_start_url = "https://mvg.jp/actress/detail/17816"
movie_selector = "div.swiper-slide a.item"
movie_next_selector = "a[rel='next']"


client = MongoClient(mongo_url)
db = client[db_name]
movie_collection = db["movie"]
actress_collection = db["actress"]

all_proxies = get_all_proxy_name()


class ImageDownloadError(Exception):
    """自定义异常：网络相关的图片下载失败时抛出"""
    def __init__(self, doc_code, url, error):
        self.doc_code = doc_code
        self.url = url
        self.error = error
        self.message = f"下载图片失败: {url} - 错误: {error}"
        super().__init__(self.message)
        
        
def mvg_actors_parser(item):
        link = item.select_one("a").get("href")
        avatar_small = item.select_one("img.c-main-bg").get("data-src")
        japan_name = item.select_one("p.name").get_text()
        roman_name = item.select_one("p.en").get_text()
        return {
            "publisher": "mvg",
            "link": urljoin(actor_url, link),
            "avatar_small": avatar_small,
            "japan_name": japan_name,
            "roman_name": roman_name
        }
        
def mvg_movies_parser(item):
        # print(item)
        link = item.get("href")
        return {
            "link": link,
        }
        
mvg_actor_detail_parser_dict = {
    "avatar": ['img.u-hidden--sp', "data-src"],
    "profile": ['div.table', "html"],
}

mvg_actor_detail_additional_dict = {
    "detail_parsed": True
}


def get_movie_list_by_actor(url):
    list_results = get_list(
        url=url,
        item_selector=movie_selector,
        next_selector=movie_next_selector,
        parser=mvg_movies_parser,
        save=False,
    )
    return list_results

# 对于collection中的每一条数据，解析详情页并插入到MongoDB
def update_document(doc):
    detail_url = doc["link"]
    detail_result = parse_detail(
        url=detail_url,
        parse_dict=mvg_actor_detail_parser_dict,
        additional_dict=mvg_actor_detail_additional_dict
    )
    
    detail_result["movies"] = get_movie_list_by_actor(detail_url)
    
    if detail_result:
        doc.update(detail_result)
        print("详情页解析结果：", detail_result)
        return doc
    


def update_all_documents(collection_name="actress", selector = "mvg",sleep_time = 1):
    # 连接 MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]
    # 更新所有文档publisher为mvg的文档
    count = 0
    for doc in collection.find({"publisher": selector, "detail_parsed": {"$ne": True}}):
        count+=1
        updated_doc = update_document(doc)
        if updated_doc:
            collection.update_one({"_id": doc["_id"]}, {"$set": updated_doc})
            print(f"{doc['_id']}文档更新完成")
        # time.sleep(1)
            
        else:
            print(f"{doc['_id']}文档更新失败")
        time.sleep(sleep_time)
    print("全部更新完成")
    
def get_movie_code_from_url(url):
    # https://mvg.jp/works/detail/SOE245?page_from=actress&sys_code=6799
    # get -> SOE245
    return url.split("detail/")[-1].split("?")[0]



def movie_link_parser(url):
    addition_dict = {
        "code": get_movie_code_from_url(url),
        "publisher": "mvg",
        "link": url
    }
    
    parse_dict = {
        "title": ['h2.p-workPage__title', "text"],
        "description": ['p.p-workPage__text', "text"],
        "profile": ['div.p-workPage__table', "html"],
        "screenshots": ['img.swiper-lazy','list-src']
    }

    detail_result = parse_detail(
        url=url,
        parse_dict=parse_dict,
        additional_dict=addition_dict
    )
    
    return detail_result




def save_movie_to_mongo(movie_detail_dict):
    if movie_collection.find_one({"code": movie_detail_dict["code"]}):
        print(f"已存在 code 为 {movie_detail_dict['code']} 的数据，跳过")
        movie_id = movie_collection.find_one({"code": movie_detail_dict["code"]})["_id"]
        return movie_id 
    inserted_id = movie_collection.insert_one(movie_detail_dict).inserted_id
    # print(inserted_id)
    # print(f"已插入 MongoDB 文档到 movie，_id: {inserted_id}")
    return inserted_id

def update_document_movies(doc):
    movie_list = doc["movies"]
    for movie in movie_list:
        if movie.get("parsed"):
            continue
        code = get_movie_code_from_url(movie["link"])
        movie_id = movie_collection.find_one({"code": code})
        if movie_id:
            movie["id"] = str(movie_id)
            movie["parsed"] = True
            print(f"{movie['link']}已存在，跳过")
            continue
        detail_result = movie_link_parser(movie["link"])
        if detail_result:
            # 将movie存入movie的colletion，并将_id插入替换原本的{"link":link,'id':_id}
            # 添加一个字段{"movie_parsed":True}
            # 更新原本的movies字段
            inserted_id = save_movie_to_mongo(detail_result)
            movie["id"] = str(inserted_id)
            movie["parsed"] = True
            print(f"{movie['link']}详情页解析结果：成功,{movie['id']}")
        else:
            print(f"{movie['link']}解析失败")
    # return 
    doc['movies_parsed'] = True
    return doc

def update_all_documents_movies(selector = "mvg"):

    # 更新所有文档publisher为mvg的文档
    count = 0
    for doc in actress_collection.find({"publisher": selector, "movies_parsed": {"$ne": True},"detail_parsed":True}):
        count+=1
        updated_doc = update_document_movies(doc)
        if updated_doc:
            actress_collection.update_one({"_id": doc["_id"]}, {"$set": updated_doc})
            print(f"{doc['_id']}文档更新完成")       
        else:
            print(f"{doc['_id']}文档更新失败")

    print("全部更新完成")
    
def download_image(session, url, doc_code, index, save_folder):
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
        folder = os.path.join(save_folder, image_hash[:2], image_hash[2:4])
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
    
    
    
def download_movie_image_and_change_url_to_local(selector='mvg', 
                                                 save_folder=r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\movie",
                                                 max_workers=5):
    """
    下载 MongoDB 中符合条件的文档的 screenshots 图片，并将 URL 替换为本地路径。
    仅在网络相关的图片下载失败时抛出异常，其他错误跳过。

    :param selector: 发布者选择器
    :param save_folder: 本地保存图片的根目录
    :param mongo_url: MongoDB 连接 URL
    :param db_name: MongoDB 数据库名称
    :param collection_name: MongoDB 集合名称
    :param max_workers: 并行线程数
    :raises ImageDownloadError: 如果任意图片下载失败
    """

    collection = movie_collection
    count = 0

    # 使用 requests.Session 复用 TCP 连接
    with requests.Session() as session, ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 查找符合条件的文档
        for doc in collection.find({"publisher": selector, "image_parsed": {"$ne": True}}):
            count += 1
            doc_code = doc.get('code', 'unknown_code')
            print(f"开始下载第{count}个文档: {doc_code}")
            screenshots = doc.get("screenshots", [])
            if not screenshots:
                print(f"{doc_code} 没有图片")
                continue

            # 提交所有图片的下载任务
            futures = {}
            for i, url in enumerate(screenshots):
                if url.startswith("http"):
                    future = executor.submit(download_image, session, url, doc_code, i, save_folder)
                    futures[future] = i
                else:
                    print(f"非 HTTP URL，跳过: {url}")
                    screenshots[i] = None  # 非 HTTP URL 设置为 None

            # 收集下载结果
            for future in as_completed(futures):
                i = futures[future]
                try:
                    new_url = future.result()
                    if new_url:
                        screenshots[i] = new_url
                    else:
                        print(f"图片保存失败，URL: {screenshots[i]}")
                        screenshots[i] = None  # 保存失败，设置为 None
                except ImageDownloadError as e:
                    print(e)
                    # 中断整个过程
                    raise e
                except Exception as e:
                    print(f"下载图片时发生未预期的错误: {e}")
                    # 中断整个过程，或根据需求选择跳过
                    raise e

            # 更新文档
            doc["screenshots"] = screenshots
            doc["image_parsed"] = True
            try:
                collection.update_one({"_id": doc["_id"]}, {"$set": doc})
                print(f"{doc_code} 图片下载并更新完成")
            except Exception as e:
                print(f"更新 MongoDB 文档失败: {doc_code} - 错误: {e}")
                # 根据需求选择是否中断或继续
                continue  # 这里选择继续

    print("全部下载完成")
    return True 
                
                    
def download_actress_image_and_change_url_to_local(selector='mvg', save_folder = r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\actress"):
    collection = actress_collection
    
    for doc in collection.find({"publisher": selector, "image_parsed": {"$ne": True}}):
        url = doc["avatar"]
        response = requests.get(url)
        if response.status_code == 200:
            image = response.content
            extend_name = url.split(".")[-1]
            image_name = f"{doc['japan_name']}.{extend_name}"
            # hash image
            image_hash = hashlib.md5(image).hexdigest()
            # 两层hash文件夹，每层用两个字母
            folder = os.path.join(save_folder, image_hash[0])
            if not os.path.exists(folder):
                os.makedirs(folder)
            image_path = os.path.join(folder, image_name)
            with open(image_path, "wb") as f:
                f.write(image)
            doc["avatar"] = image_path
            doc["image_parsed"] = True
            collection.update_one({"_id": doc["_id"]}, {"$set": doc})
            print(f"{doc['japan_name']}图片下载完成")
        else:
            print(f"{doc['japan_name']}图片下载失败")
    print("全部下载完成")
    return True 
        

if __name__ == "__main__":
    update_all_documents()
    
    
    # 更新所有文档的movies字段
    
    
    # 更新所有文档的图片字段
    result = False  
    document_flag = True 
    while not result :
        if len(all_proxies) == 0:
            all_proxies = get_all_proxy_name()
        while switch_proxy(all_proxies.pop()) == False:
            time.sleep(1)
            continue 
        
        if document_flag:
            try:
                result = download_movie_image_and_change_url_to_local()
            except ImageDownloadError as e:
                print(e)
                continue
        else:
            try:
                document_flag = update_all_documents_movies()
            except Exception as e:
                print(e)
                continue
