import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin
from pprint import pprint

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


def parse_detail(url, parse_dict, additional_dict):
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