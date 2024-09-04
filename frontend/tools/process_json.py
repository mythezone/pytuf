import os, sys , json
import requests 
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from frontend.tools.base import get_response_by_url, sessions, new_session, headers, save_resource_by_url


javdb_base = "https://javdb.com"
def process_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.endswith(".json"):
                file_path = os.path.join(root,f)
                process_json(file_path)
                
    

def process_json(file_path=None,j=None):
    if j is None:
        folder = os.path.dirname(file_path)
        j = json.load(open(file_path,"r",encoding="utf-8"))
    else:
        folder = j["folder"]
        file_path = os.path.join(folder, j["code"]+".json")
    os.makedirs(folder,exist_ok=True)
    if j.get("processed", False):
        print("Already processed")
        return 
    
    try:
        if j.get("video_src",None) is not None and j["video_src"]!="":
            video_pre = j["video_src"]
            if video_pre.startswith("http"):
                video_url = video_pre
            elif video_pre.startswith("//"):
                video_url = "https:"+video_pre
            else:
                video_url = ""
                
            if video_url != "":
                print("downloading video: ",video_url)
                video_file = os.path.join(folder,os.path.basename(video_url))
                if os.path.exists(video_file):
                    pass 
                else:
                    save_resource_by_url(video_url,video_file)
    except Exception as e:
        print(e)
        print(f"Video error in {file_path}")
        
        
    try:          
        if j.get("cover",None) is not None and j.get("cover",None)!="":
            
            cover_url = j["cover"]
            cover_file = os.path.join(folder,"cover.jpg")
            if os.path.exists(cover_file):
                pass    
            else:
                save_resource_by_url(cover_url,cover_file)
    except Exception as e:
        print(e)
        print(f"Cover error in {file_path}")
      
    try: 
        if j.get("images",None) is not None:
            print("Downloading images")
            screenshot = j["images"]
            new_images = []
            for img_url in screenshot:
                img_file = os.path.join(folder,"screenshot",os.path.basename(img_url))
                if os.path.exists(img_file):
                    pass
                else:
                    os.makedirs(os.path.dirname(img_file),exist_ok=True)
                    save_resource_by_url(img_url,img_file)
                    # response = requests.get(img_url,headers=header)
                    
                    # with open(img_file,"wb") as f:
                    #     f.write(response.content)
                    new_images.append(img_file)
            j["images"] = new_images
    except Exception as e:
        print(e)
        print(f"Screenshot error in {file_path}")
    
    try:   
        
        if j.get("related",None) is not None:       
            print("Downloading related")        
            related = j["related"]
            for r in related:
                r_file = os.path.join(folder,"related",os.path.basename(r["img"]))
                if os.path.exists(r_file):
                    pass
                else:
                    os.makedirs(os.path.dirname(r_file),exist_ok=True)
                    save_resource_by_url(r["img"],r_file)
                    # response = requests.get(r["img"])
                    # with open(r_file,"wb") as f:
                    #     f.write(response.content)
                # j["related"][idx]["img"] = r_file
    except Exception as e:
        print(e)
        print(f"Related error in {file_path}")
    
    try:
        if j.get("may_like",None) is not None:
            print("Downloading may like")
            liked = j["may_like"]

            for r in liked:
                r_file = os.path.join(folder,"may_like",os.path.basename(r["img"]))
                if os.path.exists(r_file):
                    pass
                else:
                    os.makedirs(os.path.dirname(r_file),exist_ok=True)
                    save_resource_by_url(r["img"],r_file)
                    # response = requests.get(r["img"])
                    # with open(r_file,"wb") as f:
                    #     f.write(response.content)
                # j["may_like"][idx]["img"] = r_file
    except Exception as e:
        print(e)
        print(f"May like error in {file_path}")
    
                
    j["processed"] = True
    with open(file_path,"w",encoding="utf-8") as f:
        print("saving file: ",file_path)
        json.dump(j,f,ensure_ascii=False,indent=4)
                
if __name__ == "__main__":
    process_json(r"\\10.16.12.105\disk\G\Info\A\ATI\ATID-399\ATID-399.json")
            
    