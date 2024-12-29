from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from clawer import *
import time 
from change_proxy import *
from mvg import * 

def crawl_and_save_actress_list():
    """
    阶段1：爬取所有 mvg actress 列表并存储到 'actress_collection'.
    """
    all_start_urls = [
        "https://mvg.jp/actress/a",
        "https://mvg.jp/actress/ka",
        "https://mvg.jp/actress/sa",
        "https://mvg.jp/actress/ta",
        "https://mvg.jp/actress/na",
        "https://mvg.jp/actress/ha",
        "https://mvg.jp/actress/ma",
        "https://mvg.jp/actress/ya",
        "https://mvg.jp/actress/ra",
        "https://mvg.jp/actress/wa"
    ]
    # 遍历所有起始URL
    for url in all_start_urls:
        print("[Actress] Start to crawl:", url)
        # 利用现有 get_list 函数
        get_list(
            url=url,
            item_selector="div.p-hoverCard",
            next_selector="a[rel='next']",
            parser=mvg_actors_parser,
            save=True,  # 入库
            key="link",  # 避免重复
            collection_name="actress"  # 存入actress_collection
        )
        # time.sleep(1)  # 避免过快请求，可视情况而定
    print("[Actress] 所有分页爬取完成。")
    
def parse_actress_detail_and_update():
    """
    阶段2：解析actress_collection中未解析(detail_parsed != True)的文档，获取Profile和Movies等信息。
    """
    coll = db["actress"]
    for doc in coll.find({"publisher": "mvg", "detail_parsed": {"$ne": True}}):
        updated_doc = update_document(doc)  # 内部会 parse_detail -> mvg_actor_detail_parser_dict -> get_movie_list_by_actor
        if updated_doc:
            coll.update_one({"_id": doc["_id"]}, {"$set": updated_doc})
            print(f"[Actress Detail] {doc['_id']} 文档更新完成")
        else:
            print(f"[Actress Detail] {doc['_id']} 文档更新失败")
    print("[Actress Detail] 全部解析完成。")
    
def parse_movies_by_actress():
    """
    阶段3：从 actress_collection 的 movies 字段中，逐条解析 movie 信息，存储到 movie_collection.
    """
    coll_actress = db["actress"]
    for doc in coll_actress.find({"publisher": "mvg", "movies_parsed": {"$ne": True}, "detail_parsed": True}):
        updated_doc = update_document_movies(doc)  # 内部遍历 doc["movies"]
        if updated_doc:
            coll_actress.update_one({"_id": doc["_id"]}, {"$set": updated_doc})
            print(f"[Actress -> Movies] {doc['_id']} 文档更新完成")
        else:
            print(f"[Actress -> Movies] {doc['_id']} 文档更新失败")
    print("[Actress -> Movies] 全部电影解析完成。")
    
def download_all_movies_screenshots():
    """
    阶段4：从 movie_collection 中，下载所有尚未下载截图的记录 (image_parsed != True)。
    遇到网络错误抛出异常，触发代理切换。
    """
    try:
        result = download_movie_image_and_change_url_to_local(
            selector="mvg",  # 只处理 publisher=mvg
            save_folder=r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\movie"
        )
        if result:
            print("[Movie Screenshots] 截图全部下载完成。")
    except ImageDownloadError as e:
        # 这里抛出网络相关异常
        print("[Movie Screenshots] 出现网络错误，准备切换代理。")
        raise e
    
def main_workflow():
    

    # Step 4: 下载 Movie 截图并更新
    # 需要防止网络错误 -> 切换代理
    all_proxies = get_all_proxy_name()
    while True:
        try:
            # Step 1: 爬取 Actress 列表
            # crawl_and_save_actress_list()

            # Step 2: 解析 Actress 详情
            parse_actress_detail_and_update()

            # Step 3: 解析 Movie 详情
            parse_movies_by_actress()
        except Exception as e:
            print("[Workflow] 出现异常：", e)
            # 根据需要决定是否继续重试或退出
            pass 
        
        if not all_proxies:
            print("[Proxy] 代理用尽，重新获取或退出。")
            all_proxies = get_all_proxy_name()
            if not all_proxies:
                print("[Proxy] 无可用代理，退出。")
                break

        current_proxy = all_proxies.pop()
        switched = switch_proxy(current_proxy)
        if not switched:
            print(f"[Proxy] 切换到 {current_proxy} 失败，尝试下一个代理。")
            continue

        try:
            print(f"[Proxy] 已切换到 {current_proxy}")
            download_all_movies_screenshots()
            # 如果成功，无异常抛出，则跳出循环
            print("[Workflow] 全部流程完成。")
            break
        except ImageDownloadError:
            print("[Workflow] 网络异常，继续切换代理重试。")
            # 此时回到 while True 顶部，弹出下一个代理
            continue
        except Exception as e:
            print("[Workflow] 出现其他异常：", e)
            # 根据需要决定是否继续重试或退出
            break
        
        
if __name__ == "__main__":
    main_workflow()




