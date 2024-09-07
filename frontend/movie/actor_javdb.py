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
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
        
    # print(url)
    response = requests.get(url,headers=header)
    # print(response.text)
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
    process_list("/actors/ZX5z7")
    