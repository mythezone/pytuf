import requests
import hashlib
import os 
from mongo import *
from change_proxy import *

class ImageDownloadError(Exception):
    """自定义异常：网络相关的图片下载失败时抛出"""
    def __init__(self, doc_code, url, error):
        self.doc_code = doc_code
        self.url = url
        self.error = error
        self.message = f"下载图片失败: {url} - 错误: {error}"
        super().__init__(self.message)

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
    
def download_movie_image_and_change_url_to_local(save_folder):
    actress_collection = get_collection("actress")
    session=requests.Session()
    
    for doc in actress_collection.find({"avatar_parsed": {"$ne": True}}):
        doc_code = doc["japan_name"]
        doc_id = doc["_id"]
        url = doc["avatar"]
        if not url:
            continue # 跳过空 URL
        new_url = download_image(
            session=session,
            url=url,
            doc_code=doc_code,
            index="avatar",
            save_folder=save_folder
        )
        if new_url:
            # 更新图片 URL
            doc["avatar"] = new_url
            doc["avatar_parsed"] = True
    # 更新文档
        result = actress_collection.replace_one({"_id": doc_id}, doc)
        if result.modified_count:
            print(f"[Actress -> Movies] {doc['_id']} 文档更新完成")
        else:
            print(f"[Actress -> Movies] {doc['_id']} 文档更新失败")
    print("[Actress -> Movies] 全部图片下载完成。")
    return True # 全部下载完成
    
    
def main():
    all_proxies = get_all_proxy_name()
    save_folder = r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\actress"
    update_all_del_attr("actress", {}, "avatar_small")
    while True:
        try:
            download_movie_image_and_change_url_to_local(save_folder)
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
            download_movie_image_and_change_url_to_local(save_folder)
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
    main()