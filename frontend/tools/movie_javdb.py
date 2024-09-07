import bs4
import requests
from pprint import pprint
import os, sys , json
# from movie.models import Movie
import time 
from tqdm import tqdm
import random 

import sys,os,json
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from frontend.tools.process_json import process_json

from frontend.tools.base import get_response_by_url, sessions, new_session, headers, save_resource_by_url  

def multi_pipeline(file_path, info_path=r"\\10.16.12.105\disk\G\Info"): 
    
    try:
        wait_time = 0 
        for root, dirs, files in os.walk(file_path): 
            print("Start processing files in ", root)
            files = [x for x in files if x.endswith(".mp4") or x.endswith(".mkv")]

            for file in files:
                print("File:",file)
                if file[0] in ["0","1","2","3","4","5","6","7","8","9","F","P"]:
                    continue
                
                file_size = os.path.getsize(os.path.join(root,file))
                if file_size > 500*1024*1024:
                    wait_time = single_pipeline(os.path.join(root,file),info_path)

                if wait_time!= 0:
                    time.sleep(wait_time)
                    
    except Exception as e:
        print(e)
        print("Error in processing files folder, retry after 200 seconds.")
        time.sleep(200)


def get_info_path_by_code(code, info_path=r"\\10.16.12.105\disk\G\Info"):
    
    first_letter = code[0]
    first_3_letters = code[:3]
    folder = os.path.join(info_path,first_letter,first_3_letters,code)
    os.makedirs(folder,exist_ok=True)
    return folder


def single_pipeline(file_path, info_path=r"\\10.16.12.105\disk\G\Info"):
    file_name = os.path.basename(file_path)
    
    code = file_name.split(".")[0]
    
    first_letter = file_name[0]
    first_3_letters = file_name[:3]
    folder = os.path.join(info_path,first_letter,first_3_letters,code)
    if not os.path.exists(folder):
        os.makedirs(folder,exist_ok=True)
        
    json_file = os.path.join(folder,f"{code}.json")
    html_file = os.path.join(folder,f"javdb_{code}.html")
    
    if os.path.exists(json_file):
        with open(json_file,'r',encoding="utf-8") as f:
            json_dict = json.load(f)
            if json_dict.get("processed",False):
                return 0
    else:
        href = get_href_by_code(code)
        if href is None:
            print(f"cant get url by code:{code}")
            return 5
        
        try:
            json_dict = get_movie_json_by_url(href=href,html_file=html_file)
            json_dict["video_path"] = file_path
        except Exception as e:
            print(f"cant get movie json by url:{href}")

            print(e)
            return 10
    
        with open(json_file,"w",encoding="utf-8") as f:
            json.dump(json_dict,f,ensure_ascii=False,indent=4)
    try:
        process_json(file_path=json_file)
    except Exception as e:
        print(e)
        print(f"Error in processing json file:{json_file}")
        return 10
    
    return random.randint(10,20)

def get_href_by_code(code):
    url = f"https://javdb.com/search?q={code}"

    try:
        response = get_response_by_url(url)
    except Exception as e:
        print(e)
        print(f"Error in getting response from url:{url}")
        return None 
    
    if response.status_code != 200:
        print(f"Error in getting response from url:{url}")
        return None
    
    text = getattr(response, "text",None)
    
    if text is None:
        print(f"No text found in response from url:{url}")
        return 

    soup = bs4.BeautifulSoup(text, "html.parser")
    
    
    movie_list = soup.find_all("div", class_="item")
    if len(movie_list) == 0:
        return None
    first_movie = movie_list[0]
    movie_href = first_movie.a["href"]
    # url = f"https://javdb.com{movie_href}"
    return movie_href

def get_movie_json_by_url(href=None,url=None, html_file=True):
    info = {
            "id": href
        }
    if href is None and url is None:
        return {}
    
    if href:
        url = f"https://javdb.com{href}"
        info["file_path"] = ""
        

    
    if html_file is str and os.path.exists(html_file):
        with open(html_file,"r",encoding="utf-8") as f:
            soup = bs4.BeautifulSoup(f.read(),"html.parser")
    else:
        response = get_response_by_url(url)
    if response.status_code > 300:
        print(f"Error in getting response from url:{url}")
        return info
    text = getattr(response, "text",None)
    if text is None:
        print(f"No text found in response from url:{url}")
        return info
    
    soup = bs4.BeautifulSoup(response.text, "html.parser")
        
        
    video_detail = soup.find("div",{"class":"video-detail"})

    
    if video_detail is not None:
        try:
            
            code = video_detail.find("strong").text.strip()
            info["code"] = code
            info["folder"] = get_info_path_by_code(code)
            with open(os.path.join(info["folder"],"javdb_"+info["code"]+".html"),"w",encoding="utf-8") as f:
                f.write(response.text)
        except Exception as e:
            print(f"No code found:{info['id']}")
            info["code"] = ""
        
        try:
            info["current-title"]=video_detail.find("strong",{"class":"current-title"}).text
        except Exception as e:
            print(f"No current title found:{info['code']}")
            info["current-title"] = ""
        
        try:
            
            info["origin-title"]=video_detail.find("span",{"class":"origin-title"}).text
        except Exception as e:
            print(f"No origin title found:{info['code']}")
            info["origin-title"] = ""
    
    
    panel_info = soup.find("nav", {"class":"movie-panel-info"})
    panel={}
    try:
        spans = panel_info.find_all("div",{"class":"panel-block"})
        
        for span in spans:
        
            try:
                key_span = span.find("strong")
                if key_span is None:
                    continue 
                else:
                    key = key_span.text.strip()[:-1]
                value =span.find("span", {"class":"value"})
                if value is None:
                    continue
                aas = value.find_all("a")
                if aas:
                    res = []
                    for a in aas:
                        if a is None: 
                            continue
                        if getattr(a,"text", None):
                            href = a["href"] 
                            t = a.text
                            res.append([t,href])
                    panel[key] = res
                else:
                    panel[key] = value.text.strip()
            except Exception as e:
                print(f"Error in parsing panel info:{info['code']}")
                print(e)
                continue
    except Exception as e:
        print(f"No panel info found:{info['code']}")
        
    info["meta"] = panel
    
    video = soup.find("video",{"id":"preview-video"})
    if video is not None:
        info['video_src'] = video.find("source")["src"]
    
    magnet_content = soup.find("div",{"id":"magnets-content"})
    try:
        if magnet_content is not None:
            magnets = []
            for magnet in magnet_content.find_all('div',{"class":"item"}):
                href = magnet.find("a")["href"]
                name = magnet.find("span",{"class":"name"}).text.strip()
                meta = magnet.find("span",{"class":"meta"}).text.strip()
                tags = [x.text.strip() for x in magnet.find_all("span",{"class":"tag"})]
                time = magnet.find("span",{"class":"time"}).text.strip()
                magnets.append({"href":href,"name":name,"meta":meta,"tags":tags,"time":time})
            
            info["magnets"] = magnets
    except Exception as e:
        print(f"No magnets found:{info['code']}")
        info["magnets"] = []

    try:
        cover_src = soup.find("img",{"class":"video-cover"})["src"]
    except Exception as e:
        print(f"No cover found:{info['code']}")
        cover_src = ""
    info["cover"] = cover_src
    
    images = soup.find("div",{"class":"message-body"}).find_all("a",{"class":"tile-item"})
    image_src = [x["href"] for x in images]
    
    image_src.insert(0,cover_src)
    info["images"] = image_src
    
    same_actors = soup.find_all("div",{"class":"tile-images tile-small"})
    if same_actors is not None:
        
        if len(same_actors)>1:
            relateds = same_actors[0].find_all("a",{"class":"tile-item"})
            may_likes = same_actors[1].find_all("a",{"class":"tile-item"})
        else:
            may_likes = same_actors[0].find_all("a",{"class":"tile-item"})
            relateds = None 
        if relateds is not None:
            relateds_res = [parse_relateds(x) for x in relateds]
        else:
            relateds_res = []
            
        if may_likes is not None:
                may_likes_res = [parse_relateds(x) for x in may_likes]
        else:
            may_likes_res = []
    
        info['related'] = relateds_res
        info['may_like'] = may_likes_res
    
    return info
    
    
def parse_relateds(related):
        res = {}
        
        res['href'] = related['href']
        res['title'] = related['title']
        
        res['img'] = related.find("img")['src']
        
        res['code'] = related.find("div",{"class":"video-number"}).text
        
        return res 
        

if __name__ == "__main__":
    # multi_pipeline(r"\\10.16.12.105\disk\G\Adult")
    # multi_pipeline(r"\\10.16.12.105\disk\D\Adult")
    # multi_pipeline(r"\\10.16.12.105\disk\J\Adult")
    # multi_pipeline(r"\\10.16.12.105\disk\media\4t\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\media\4t2\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\media\16t\Adult")