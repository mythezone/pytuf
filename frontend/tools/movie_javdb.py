import bs4
import requests
from pprint import pprint
import os, sys , json
# from movie.models import Movie
import time 
from tqdm import tqdm
import random 
from process_json import process_json


def multi_pipeline(file_path, info_path=r"\\10.16.12.105\disk\G\Info"):   
    start_time = time.time()
    while True:
        print("Start processing files in ", file_path)
        end_time = time.time()
        if end_time - start_time > 36000:
            break
        try:
            wait_time = 0 
            for root, dirs, files in os.walk(file_path): 
                print("Start processing files in ", root)
                files = [x for x in files if x.endswith(".mp4") or x.endswith(".mkv")]
                count = 0
                for file in files:
                    file_size = os.path.getsize(os.path.join(root,file))
                    if file_size > 500*1024*1024:
                        wait_time = single_pipeline(os.path.join(root,file),info_path)
                    print(f"{count+1}/{len(files)}: Processing {file} done: next file in {wait_time} seconds")
                    count+=1
                    if wait_time!= 0:
                        time.sleep(wait_time)
                        
        except Exception as e:
            print(e)
            time.sleep(200)
            continue
    


def single_pipeline(file_path, info_path=r"\\10.16.12.105\disk\G\Info"):
    file_name = os.path.basename(file_path)
    
    code = file_name.split(".")[0]
    
    first_letter = file_name[0]
    first_3_letters = file_name[:3]
    folder = os.path.join(info_path,first_letter,first_3_letters,code)
    json_file = os.path.join(folder,f"{code}.json")
    html_file = os.path.join(folder,f"javdb_{code}.html")
    if os.path.exists(json_file):
        with open(json_file,'r',encoding="utf-8") as f:
            json_dict = json.load(f)
            if json_dict.get("processed",False):
                return 0
    
    if not os.path.exists(folder):
        os.makedirs(folder,exist_ok=True)
    
    url = get_url_by_code(code)
    try:
        json_dict = get_movie_json_by_url(url, html_file)
        json_dict["video_path"] = file_path
        
        
    except Exception as e:
        print(e)
        return 10
    
    with open(json_file,"w",encoding="utf-8") as f:
        json.dump(json_dict,f,ensure_ascii=False,indent=4)
        
    if json_dict != {}:
        try:
            process_json(json_file)
        except Exception as e:
            print(e)
            return 10
    return random.randint(10,20)
        

def get_url_by_code(code):
    url = f"https://javdb.com/search?q={code}"
    header1 = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=header1)
    except Exception as e:
        print(e)
        return None 
    
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    
    
    movie_list = soup.find_all("div", class_="item")
    if len(movie_list) == 0:
        return None
    first_movie = movie_list[0]
    movie_href = first_movie.a["href"]
    # url = f"https://javdb.com{movie_href}"
    return movie_href

def get_movie_json_by_url(href, html_file=None):
    if href is None:
        return {}
    
    url = f"https://javdb.com{href}"

    response = requests.get(url)

    
    if html_file:
        with open(html_file,"w",encoding="utf-8") as f:
            f.write(response.text)
    
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    info = {
        "id": href
    }
    
    # with open("detail.html","r",encoding="utf-8") as f:
    #     soup = bs4.BeautifulSoup(f.read(),"html.parser")
    
    video_detail = soup.find("div",{"class":"video-detail"})
    
    if video_detail is not None:
        info["current-title"]=video_detail.find("strong",{"class":"current-title"}).text
        try:
            info["origin-title"]=video_detail.find("span",{"class":"origin-title"}).text
        except Exception as e:
            info["origin-title"] = ""
        code = video_detail.find("strong").text
        info["code"] = code
    
    
    panel_info = soup.find("nav", {"class":"movie-panel-info"})
    spans = panel_info.find_all("div",{"class":"panel-block"})
    panel={}
    for span in spans:
        try:
            key = span.find("strong").text.strip()[:-1]
            value =span.find("span", {"class":"value"})
            aas = value.find_all("a")
            if aas:
                res = {}
                res["href"] = [a["href"] for a in aas]
                res["text"] = [a.text for a in aas]
                panel[key] = list(zip(res["text"], res["href"]))
            else:
                panel[key] = value.text.strip()
        except Exception as e:
            pass 
        
    info["meta"] = panel
    

            
    video = soup.find("video",{"id":"preview-video"})
    if video is not None:
        info['video_src'] = video.find("source")["src"]
    
    magnet_content = soup.find("div",{"id":"magnets-content"})
    
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

    try:
        cover_src = soup.find("img",{"class":"video-cover"})["src"]
    except Exception as e:
        cover_src = ""
    info["cover"] = cover_src
    
    images = soup.find("div",{"class":"message-body"}).find_all("a",{"class":"tile-item"})
    image_src = [x["href"] for x in images]
    
    image_src.insert(0,cover_src)
    info["images"] = image_src
    
    same_actors = soup.find_all("div",{"class":"tile-images tile-small"})
    if same_actors is not None:
        relateds = same_actors[0].find_all("a",{"class":"tile-item"})
        may_likes = same_actors[1].find_all("a",{"class":"tile-item"})
        if relateds is not None:
            relateds_res = [parse_relateds(x) for x in relateds]
        if may_likes is not None:
            may_likes_res = [parse_relateds(x) for x in may_likes]
    
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
        
def parse_panel_info(panel_info):
    
    """
    {'番號:': 'ABP-123', '日期:': '2014-04-01', '時長:': '140 分鍾', '導演:': 'Porn Stars', '片商:': 'プレステージ', '發行:': 'ABSOLUTELY PERFECT', '系列:': '満足度満点ソープ', '評分:': '\xa03.43分, 由45人評價', '類別:': '巨乳,\xa0單體作品,\xa0妓女,\xa0無碼破解', '演員:': '\nさつき芽衣♀\xa0\n        瀬田一花♀\xa0\n        月野かすみ♀\xa0\n        結城りの♀\xa0\n        美波もも♀\xa0\n        乃木蛍♀\xa0\n    '}
    """
    new_info = {}
    for k,v in panel_info.items():
        if k == "番號:":
            new_info["code"] = v
        elif k == "日期:":
            new_info["release_date"] = v
        elif k == "時長:":
            new_info["duration"] = v
        elif k == "導演:":
            new_info["director"] = v
        elif k == "片商:":
            new_info["studio"] = v
        elif k == "發行:":
            new_info["publisher"] = v
        elif k == "系列:":
            new_info["series"] = v
        elif k == "評分:":
            new_info["rating"] = v
        elif k == "類別:":
            new_info["categories"] = v.split(",\xa0")
        elif k == "演員:":
            new_info["actress"] =[x.strip() for x in  v.split("\xa0\n") if x.strip() != "" and x.strip().endswith("♀")]
            new_info["actor"] = [x.strip() for x in  v.split("\xa0\n") if x.strip() != "" and x.strip().endswith("♂")]
            
    pprint(new_info)
    
def download_image(image_url, file_path):
    response = requests.get(image_url)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path
    
if __name__ == "__main__":
    multi_pipeline(r"\\10.16.12.105\disk\G\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\D\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\J\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\media\4t\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\media\4t2\Adult")
    multi_pipeline(r"\\10.16.12.105\disk\media\16t\Adult")
    
    # # parse_panel_info({'番號:': 'ABP-123', '日期:': '2014-04-01', '時長:': '140 分鍾', '導演:': 'Porn Stars', '片商:': 'プレステージ', '發行:': 'ABSOLUTELY PERFECT', '系列:': '満足度満点ソープ', '評分:': '\xa03.43分, 由45人評價', '類別:': '巨乳,\xa0單體作品,\xa0妓女,\xa0無碼破解', '演員:': '\nさつき芽衣♀\xa0\n        瀬田一花♀\xa0\n        月野かすみ♀\xa0\n        結城りの♀\xa0\n        美波もも♀\xa0\n        乃木蛍♀\xa0\n    '})
    # images = ['https://c0.jdbstatic.com/samples/yx/yxxdwd_l_0.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_1.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_2.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_3.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_4.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_5.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_6.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_7.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_8.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_9.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_10.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_11.jpg', 'https://c0.jdbstatic.com/samples/yx/yxxdwd_l_12.jpg']
    
    # for i in range(len(images)):
    #     download_image(images[i],f"static/test/image_{i}.jpg")