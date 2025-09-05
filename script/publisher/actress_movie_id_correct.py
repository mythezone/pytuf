from concurrent.futures import ThreadPoolExecutor
from mongo import *
from clawer import * 
import json 


def correct_all_movies_actress_id():
    # 1. 获取所有 Actress
    actress_collection = get_collection("actress")
    movie_collection = get_collection("movie")
    
    starter = len("{'_id': ObjectId('")
    ender = starter + len("6770ed9445fbc5c1751eed83")
    
    def task(actress):
        actress_id = actress["_id"]
        # 2. 获取所有该 Actress 的 Movie
        
        actress_name = actress["roman_name"]
        print(f"Actress: {actress_name}")
        
        actress_movies = actress["movies"]
        # print(actress_movies)

        for movie in actress_movies:
            movie_id = movie["id"]
            if len(movie_id) > len("6770ed9445fbc5c1751eed83"):
                # print(movie_id)
                movie_id = movie_id[starter:ender]
                # print(movie_id)

            else:
                continue
            
            # 3. 更新 Movie 的 Actress ID
            movie['id'] = movie_id
        
        # 4. 更新 Actress 的 Movie
        actress_collection.update_one({"_id": actress_id}, {"$set": {"movies": actress_movies}})
    
    # multi-threading
    with ThreadPoolExecutor(max_workers=10) as executor:
        for actress in actress_collection.find():
            executor.submit(task, actress)
            
def get_one_screenshot():
    movie_collection = get_collection("movie")
    session = requests.Session()
    count = 0 
    for movie in movie_collection.find({"screenshots": None}):
        count += 1
        movie_url = movie['link']
        parse_dict = {
            "screenshots": ["div.swiper-slide img", "list-src"]
        }
        
        screenshots_urls = parse_detail(movie_url, parse_dict=parse_dict)["screenshots"]
        if screenshots_urls is None:
            print(f"{count}/3159: {movie['code']} screenshot not found.")
            continue
        sfs = []
        for index, screenshots_url in enumerate(screenshots_urls):
            screenshot_filename = download_image(session=session,url = screenshots_url,doc_code=movie["code"],index=index)
            sfs.append(screenshot_filename)
            
        movie_collection.update_one({"_id": movie["_id"]}, {"$set": {"screenshots": sfs}})
        print(f"{count}/3159: {movie['code']} screenshot downloaded.")
    print("All screenshots downloaded.")
    
        
        


if __name__ == "__main__":
    get_one_screenshot()
