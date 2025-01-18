
from pymongo import MongoClient


mongo_url = "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
db_name = "myj"
collection_name = "actress"

def get_collection(collection_name=collection_name, mongo_url=mongo_url, db_name=db_name):
    """
    获取 MongoDB 集合对象。
    :param mongo_url: MongoDB 连接 URL，形如 mongodb://localhost:27017/
    :param db_name: 数据库名称
    :param collection_name: 集合名称
    :return: 集合对象
    """
    # 连接 MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]
    return collection

def update_doc(collection, updated_doc):
    """
    更新 MongoDB 文档。
    :param collection: MongoDB 集合对象
    :param updated_doc: 更新后的文档
    """
    if updated_doc:
        collection.update_one({"_id": updated_doc["_id"]}, {"$set": updated_doc})
        print(f"[Actress Detail] {updated_doc['_id']} 文档更新完成")
        return True
    else:
        print(f"[Actress Detail] {updated_doc['_id']} 文档更新失败")
        return False

def update_all_with_attr(collection_name,find_dct,key,value):
    """
    更新 MongoDB 文档。
    :param collection: MongoDB 集合对象
    :param key: 更新字段
    :param value: 更新值
    """
    collection = get_collection(collection_name)
    collection.update_many(find_dct, {"$set": {key: value}})
    print(f"所有文档更新完成")
    
def update_all_del_attr(collection_name,find_dct,key):
    """
    更新 MongoDB 文档。
    :param collection: MongoDB 集合对象
    :param key: 删除字段
    """
    collection = get_collection(collection_name)
    collection.update_many(find_dct, {"$unset": {key: ""}})
    print(f"所有文档更新完成")

# 为collection中的所有文档添加字段{"publisher"："S1S1S1"}
def add_publisher_to_mongo(mongo_url=mongo_url, db_name=db_name, collection_name=collection_name,dict = {"publisher":"s1s1s1"}):
    # 连接 MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]
    # 更新所有文档
    collection.update_many({}, {"$set": dict})

if __name__ == "__main__":
    # add_publisher_to_mongo()
    update_all_with_attr(get_collection(), "publisher", "s1s1s1")