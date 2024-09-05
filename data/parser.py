
from pprint import pprint
# Insert the path into sys.path for importing.
import sys
import os
import json 

def get_rate(rate_str):
    """ 
    "4.37分, 由601人評價"
    """
    try:
        rate = rate_str.split("分")[0]
        
    except:
        rate = 0.0
        
    try:
        rater = rate_str.split("由")[1].split("人")[0]
    except:
        rater = 0
    return float(rate_str), int(rater)

def get_duration(duration_str):
    try:
        d = duration_str.split(" ")[0]
    except:
        d = 120
    return int(d)

def parse_json(file_path):
    j = json.load(open(file_path,"r",encoding="utf-8"))
    rate, rater = get_rate(j["meta"]["評分"])
    duraion = get_duration(j["meta"]["時長"])
    movie_info = {
        "id": j["id"],
        "code": j["code"],
        "current_title": j["current_title"],
        "original_title": j["original_title"],
        "release_date": j["meta"]["日期"],
        "duration": duraion,
        "rate": rate, 
        "rater": rater,
        "video_src": j["video_src"],
        "cover": j["cover"],
        "video_path": j["video_path"],
        "processed": j["processed"]
    }

    
    

    
if __name__ == '__main__':
    parse_json(r"\\10.16.12.105\disk\G\Info\A\ABP\ABP-656\ABP-656.json")
    
    
    
    
    
    
if __name__ == '__main__':
    parse_json(r"\\10.16.12.105\disk\G\Info\A\ABP\ABP-656\ABP-656.json")