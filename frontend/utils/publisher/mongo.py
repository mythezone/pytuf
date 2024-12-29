
from pymongo import MongoClient


mongo_url = "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
db_name = "myj"
collection_name = "actress"


# 为collection中的所有文档添加字段{"publisher"："S1S1S1"}
def add_publisher_to_mongo(mongo_url=mongo_url, db_name=db_name, collection_name=collection_name,dict = {"publisher":"s1s1s1"}):
    # 连接 MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]
    # 更新所有文档
    collection.update_many({}, {"$set": dict})

if __name__ == "__main__":
    add_publisher_to_mongo()