import os,sys,json 
import requests
import bs4 
from pprint import pprint

base_url = "https://javdb.com"  
base_folder = r"\\10.16.12.105\disk\G\Info\List"

def process_list(href, pages=[2], update=True):
    s = href.split("/")
    if len(s)>=2:
        cate = href.split("/")[-2]
        code = href.split("/")[-1]
    else:
        s = s[-1]
        c = s.split("?")
        cate = c[0]
        code = c[1]
    code = code.replace("?","_")
    code = code.replace("=","_")
    
        
    save_folder = os.path.join(base_folder,cate)
    save_file = os.path.join(save_folder,code+".json")
    
    if os.path.exists(save_file) and update==False:
        print("File exists")
        return 
    else:
        os.makedirs(save_folder,exist_ok=True)
        
    
    res = []
    if pages:
        for page in pages:
            movie = process_list_page(href,page)
            if movie is None:
                break
            res.extend(movie)
    else:
        page = 1
        while True:
            movie = process_list_page(href,page)
            if movie is None:
                break
            res.extend(movie)
            page+=1

    with open(save_file,"w",encoding="utf-8") as f:
        json.dump(res,f,ensure_ascii=False,indent=4)
    return res 

        
def process_list_page(href,page=1):
    if "?" in href:
        url = f"{base_url}{href}&page={page}"
    else:
        url = f"{base_url}{href}?page={page}"
    header = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Cookie": r"list_mode=h; theme=auto; locale=zh; over18=1; _ym_uid=1722342493123399834; _ym_d=1722342493; _ym_isad=2; _rucaptcha_session_id=f0d323ae09ad0233346858d5ce6076b8; hide_app_banner=1; cf_clearance=dSP3mLKRc0_TcOqGajxIjqJr7QEVewhAtEY2.QQueog-1725326224-1.2.1.1-wLcSpMSG3gedGNmNkQcb0fLIHFT8WVEs_qxObJce7FqKqzBMLQ.4xfhMFx7WLah7FfVDTj4XSpVwVibNlyz_TWQAT2tHXFDwHHRtGFZaNRu9avdGahzEyY2ntcvIFNsI4_WMTIVWAP.Or3FTkD3z_9BpWxUuXgEdHDHKMZZp6PrtyDWIVFBLxe_zO_Lu2NBFi8_Cvt7MmgvWypN39SD5f5zkY.FtkT365HF914F9LYeG_BWO0lB_jcFFOloXvTiDPeTG41IGR3DD2q3_L1LwEeFURZ0bIsCocQrDfg7Z5GOq84.tSoPQZJZKRamCJbpA1DLSQnb_fC7b0SnQpwhDhNWU7txt2O6UbqPu.gSKPXmhYq.QuFWUuk.czsoY5Nqu8yCkVWAufVUN0MBNYPvqSw; redirect_to=%2Frankings%2Fmovies; remember_me_token=eyJfcmFpbHMiOnsibWVzc2FnZSI6IklraERaWHBxYlhwaWQwRmlhWFpyZUV4M2VGQnpJZz09IiwiZXhwIjoiMjAyNC0wOS0xMFQwMToyMToyNi4wMDBaIiwicHVyIjoiY29va2llLnJlbWVtYmVyX21lX3Rva2VuIn19--4909ddf0d1a98b0a37860f08898d3f67e98da236; _jdb_session=mS9wLeTiI3SehivqCKKkXUjjIl1xSP2ajlYL2j2dMqI2XrTj3JM2Sj7i1zPN5jUwI4Xj7lZTIgEYLoLidFDfL38ykC5X463wYLRHKJVAM80YCVTFim28U2XafAM8e0Iwp8bkPrhx0FPREzfFaHoGrlMcYY7dVpdFF%2B9ukeakSS04NfU5rGXAYTTNBhL4UANQG%2Bern68IFeB4KgpqQDtFcGn64VyyIYeVk11I4Yu0eamswi6%2BEOSgrnNaAmKQ7Hch4XyP1a1rVGxPaQzGaIWZm%2FInMRA%2FG15NvbHIfI4jep2MG3kjurlntKCmlymv9LpkO79UeKSQftqVeFAJ01RG4yKfSKS1jlyaGzm2bAh3C2r9L2ywmTipr79bgRMvVETzeohDSJOanNRzRvpU08iwa99XyuwAfB1tX3YdbP%2B2buTXMj%2BjDJ2Ci%2FkwyBHoF67Tb54YT9xY4MZnGpDGzg6j7Sp%2B--F1X9SitlVTru8ggw--wzrW5gtFGZbC96esKpjDTg%3D%3D"
    }
        

        
    print(url)
    response = requests.get(url,headers=header)
    print(response.text)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    
    movie_list = soup.find("div", {"class":"movie-list"})
    
    if movie_list is None:
        return None 
    
    movies=[]
    for movie in movie_list.find_all("div", {"class":"item"}):
        try: 
            movie_info = {}
            a = movie.find("a", {"class":"box"})
            movie_info["href"] = a['href']
            movie_info["title"] = a["title"]
            movie_info["cover"] = movie.find("img",{"loading":"lazy"})["src"]
            
            title = movie.find("div",{"class":"video-title"})
            movie_info["code"] = title.find("strong").text.strip()
            movie_info["rate"] = movie.find("div",{"class":"score"}).text.strip()
            movie_info["date"] = movie.find("div",{"class":"meta"}).text.strip()
            movies.append(movie_info)
        except Exception as e:
            print(e)
            continue
    return movies 
    
if __name__ == "__main__":
    process_list("/rankings/top")
    