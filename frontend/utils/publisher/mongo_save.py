import requests
from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId

def save_dict_to_mongo_gridfs(data_dict, 
                              mongo_url, 
                              db_name, 
                              collection_name, 
                              image_fields=None):
    """
    将一个dict保存到MongoDB。如果其中包含(avatar、cover 等)图片链接字段，
    则先下载图片并存入 GridFS，将返回的 file_id 存到 dict 的同名字段中。
    
    :param data_dict: 待保存的字典
    :param mongo_url: MongoDB连接URL，形如 mongodb://localhost:27017/
    :param db_name: 数据库名称
    :param collection_name: 主集合名称 (存储业务文档)
    :param image_fields: 需要被识别为“图片链接”的字段列表(默认["avatar", "cover"])
    :return: 插入后的文档 _id
    """
    if image_fields is None:
        image_fields = ["avatar", "cover"]  # 可以根据需求自行扩展

    # 连接 MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]
    gf = GridFS(db)  # 初始化GridFS对象，默认存储在 fs.files / fs.chunks

    # 遍历需要识别为图片下载的字段
    for field in image_fields:
        if field in data_dict and isinstance(data_dict[field], str) \
           and data_dict[field].startswith("http"):
            image_url = data_dict[field]
            try:
                resp = requests.get(image_url, timeout=10)
                if resp.status_code == 200:
                    # 将下载的图片数据保存到 GridFS，并获取 file_id
                    # 注意：可额外传入 filename, contentType, metadata 等自定义字段
                    file_id = gf.put(resp.content, filename=f"{field}.jpg")
                    # 用GridFS的file_id替换原始URL
                    data_dict[field] = file_id
                else:
                    print(f"下载 {image_url} 失败，状态码: {resp.status_code}")
                    data_dict[field] = None
            except requests.exceptions.RequestException as e:
                print(f"下载 {image_url} 出错: {e}")
                data_dict[field] = None

    # 将处理完的dict插入MongoDB，返回 _id
    inserted_id = collection.insert_one(data_dict).inserted_id
    print(f"已插入MongoDB文档到 {collection_name}，_id: {inserted_id}")
    return inserted_id


# ==============
# 使用示例
# ==============
if __name__ == "__main__":
    example_dict = {
        "name": "Alice",
        "avatar": "https://example.com/images/alice_avatar.jpg",
        "cover": "https://example.com/images/alice_cover.jpg",
        "description": "Some user info"
    }

    mongo_url = "mongodb://localhost:27017/"
    db_name = "test_db"
    collection_name = "users"

    doc_id = save_dict_to_mongo_gridfs(
        data_dict=example_dict,
        mongo_url=mongo_url,
        db_name=db_name,
        collection_name=collection_name
    )
    print("插入完成，返回的 _id:", doc_id)
