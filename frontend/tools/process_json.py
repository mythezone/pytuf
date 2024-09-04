import os, sys , json
import requests 

javdb_base = "https://javdb.com"
def process_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.endswith(".json"):
                file_path = os.path.join(root,f)
                process_json(file_path)
                
    

def process_json(file_path):
    folder = os.path.dirname(file_path)
    j = json.load(open(file_path,"r",encoding="utf-8"))
    if j.get("processed", False):
        print("Already processed")
        return 
    if j.get("video_src",None) is not None:
        video_pre = j["video_src"]
        header = {  
            "Referer":javdb_base,
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        if video_pre.startswith("http"):
            video_url = video_pre
        elif video_pre.startswith("//"):
            video_url = "https:"+video_pre
        else:
            video_url = ""
            
        if video_url != "":
            video_file = os.path.join(folder,os.path.basename(video_url))
            if os.path.exists(video_file):
                pass 
            else:
                response = requests.get(video_url,headers=header)
                with open(video_file,"wb") as f:
                    f.write(response.content)
                    
    
    if j.get("cover",None) is None:
        cover_url = j["cover"]
        cover_file = os.path.join(folder,"cover.jpg")
        if os.path.exists(cover_file):
            pass    
        else:
            response = requests.get(cover_url,headers=header)
            with open(cover_file,"wb") as f:
                f.write(response.content)
      
      
    if j.get("images",None) is not None:
        screenshot = j["images"]
        new_images = []
        for img_url in screenshot:
            img_file = os.path.join(folder,"screenshot",os.path.basename(img_url))
            if os.path.exists(img_file):
                pass
            else:
                os.makedirs(os.path.dirname(img_file),exist_ok=True)
                
                response = requests.get(img_url,headers=header)
                
                with open(img_file,"wb") as f:
                    f.write(response.content)
                new_images.append(img_file)
        j["images"] = new_images
                
    if j.get("related",None) is not None:               
        related = j["related"]
        for idx,r in enumerate(related):
            r_file = os.path.join(folder,"related",os.path.basename(r["img"]))
            if os.path.exists(r_file):
                pass
            else:
                os.makedirs(os.path.dirname(r_file),exist_ok=True)
                response = requests.get(r["img"])
                with open(r_file,"wb") as f:
                    f.write(response.content)
            j["related"][idx]["img"] = r_file
    
    if j.get("may_like",None):
        liked = j["may_like"]

        for idx, r in enumerate(liked):
            r_file = os.path.join(folder,"may_like",os.path.basename(r["img"]))
            if os.path.exists(r_file):
                pass
            else:
                os.makedirs(os.path.dirname(r_file),exist_ok=True)
                response = requests.get(r["img"])
                with open(r_file,"wb") as f:
                    f.write(response.content)
            j["may_like"][idx]["img"] = r_file
    
                
    j["processed"] = True
    with open(file_path,"w",encoding="utf-8") as f:
        json.dump(j,f,ensure_ascii=False,indent=4)
                
if __name__ == "__main__":
    process_json(r"\\10.16.12.105\disk\G\Info\A\ATI\ATID-399\ATID-399.json")
            
    