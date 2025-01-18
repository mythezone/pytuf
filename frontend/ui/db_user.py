from pymongo import MongoClient
import hashlib


mongo_url = "mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin"
db_name = "myj"
collection_user = "user"


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = self.hashed_password(username, password)
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_user]
        
        self.user = self.get_user()
        

    def hashed_password(self, username, password):
        return hashlib.md5((username+password).encode()).hexdigest()

    def get_user(self):
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
        collection = db[collection_user]
        user = collection.find_one({"username": self.username})
        if user:
            if user["password"] != self.password:
                print(f"[User] {self.username} 密码错误")
                return None 
            else:
                print(f"[User] {self.username} 登录成功")
                return user
        else:
            print(f"[User] {self.username} 不存在")
            return self.add_user()
            


    def add_user(self):
        """
        更新 MongoDB 文档。
        :param collection: MongoDB 集合对象
        :param updated_doc: 更新后的文档
        """

        user = self.collection.insert_one(
                {
                    "username": self.username, 
                    "password": self.password,
                    "fav_movies": [],
                    "fav_actress": [],
                    "hate_actress": [],
                    "hate_movies": [],
                    "visted_movies": [],
                    "visted_actress": []
                    }
                )
        if user:
            
            print(f"[User] {self.username} 添加完成")
            return user 
        else:
            print(f"[User] {self.username} 添加失败")
            return None 
        
    def __str__(self):
        return self.username 
    
        
    def add_movie(self, movie_id, set_name):
        self.collection.update_one({"_id": self.user["_id"]}, {"$addToSet": {set_name: movie_id}})
        print(f"[User] {self.username} 添加 {movie_id} 完成")
        
    def del_movie(self, movie_id, set_name):
        self.collection.update_one({"_id": self.user["_id"]}, {"$pull": {set_name: movie_id}})
        print(f"[User] {self.username} 删除 {movie_id} 完成")
        
    def get_movies(self, set_name):
        movies = self.collection.find_one({"_id": self.user["_id"]}, {set_name: 1})
        return movies[set_name]
        
    def add_actress(self, actress_id, set_name):
        self.collection.update_one({"_id": self.user["_id"]}, {"$addToSet": {set_name: actress_id}})
        print(f"[User] {self.username} 添加 {actress_id} 完成")
    
    def del_actress(self, actress_id, set_name):
        self.collection.update_one({"_id": self.user["_id"]}, {"$pull": {set_name: actress_id}})
        print(f"[User] {self.username} 删除 {actress_id} 完成")
        
    def get_actress(self, set_name):
        actress = self.collection.find_one({"_id": self.user["_id"]}, {set_name: 1})
        return actress[set_name]
    
        

    
if __name__ == "__main__":
    user = User("mythezone", "")
    
    
#     user.add_movie("5f5b3b3b7b3b3b3b3b3b3b3b", "fav_movies")
#     movies = user.get_movies("fav_movies")
#     print(movies)
    