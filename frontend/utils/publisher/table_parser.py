from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient
from bs4 import BeautifulSoup

from mongo import * 
from pprint import pprint

def movie_table_html_to_dict(table_html):
    """
    将 HTML 表格转换为字典。
    :param table_html: HTML 表格字符串
    :return: 字典列表
    example:
    

    """
    if table_html is dict:
        print("table_html is dict, pass.")
        return table_html
    
    soup = BeautifulSoup(table_html, "html.parser")
    items = soup.select(".p-workPage__table .item")
    results = {}
    for item in items:
        th = item.select_one(".th")
        td = item.select_one(".td")
        if th and td:
            key = th.get_text(strip=True)
            if key in ['女優','ジャンル',]:
                tags = td.select("a.c-tag")
                value = [tag.get_text(strip=True) for tag in tags]
            else:
                if key in ['価格','収録時間','品番']:
                    value = td.select_one("p").get_text(strip=True)
                else:
                    value = td.get_text(strip=True)             
            results[key] = value
            
    return results


def actress_table_html_to_dict(table_html):
    """
    将 HTML 表格转换为字典。
    :param table_html: HTML 表格字符串
    :return: 字典列表
    example:
    <div class="table">
 <div class="item">
  <p class="th">
   身長
  </p>
  <p class="td">
   150cm
  </p>
 </div>
 <div class="item">
  <p class="th">
   3サイズ
  </p>
  <p class="td">
   B90cm (G) W58cm H84cm
  </p>
 </div>
</div>

    """
    if table_html is dict:
        return table_html
    
    soup = BeautifulSoup(table_html, "html.parser")
    items = soup.select(".table .item")
    results = {}
    for item in items:
        th = item.select_one(".th")
        td = item.select_one(".td")
        if th and td:
            key = th.get_text(strip=True)
            value = td.get_text(strip=True)             
            results[key] = value
            
    return results

def update_all_movie_profile():
    """
    更新所有电影的 Profile 字段。
    """
    coll = get_collection("movie")
    # multi-threading
    def update_movie_profile(doc):
        profile = doc['profile']
        if profile:
            updated_profile = movie_table_html_to_dict(profile)
            coll.update_one({"_id": doc["_id"]}, {"$set": {"profile": updated_profile,"profile_parsed":True}})
            print(f"Movie {doc['_id']} profile updated.")
            
    with ThreadPoolExecutor(max_workers=10) as executor:
        for doc in coll.find({"profile": {"$ne": None}}):
            executor.submit(update_movie_profile, doc)
    
    print("All movies' profile updated.")
    

    
def update_all_actress_profile():
    """
    更新所有女优的 Profile 字段。
    """
    coll = get_collection("actress")
    # multi-threading
    def update_actress_profile(doc):
        profile = doc['profile']
        if profile:
            updated_profile = actress_table_html_to_dict(profile)
            coll.update_one({"_id": doc["_id"]}, {"$set": {"profile": updated_profile,"profile_parsed":True}})
            print(f"Actress {doc['_id']} profile updated.")
            
    with ThreadPoolExecutor(max_workers=10) as executor:
        for doc in coll.find({"profile": {"$ne": None}}):
            executor.submit(update_actress_profile, doc)
    
    print("All actress' profile updated.")



    
if __name__ == "__main__":
    # update_all_movie_profile()
    # update_all_with_attr("movie",{"profile_parsed":{'$ne':True}}, "profile_parsed",True)
    update_all_actress_profile()

