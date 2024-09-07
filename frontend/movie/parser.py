
from pprint import pprint
# Insert the path into sys.path for importing.
import sys
import os
import json 
import shutil

sys.path.append(r"C:\Users\mythezone\Documents\project\python\pytuf\frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend.settings')
import django  
django.setup()

from movie.models import Movie, Magnet
from person.models import Group

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
        
    return float(rate), int(rater)

def get_duration(duration_str):
    try:
        d = duration_str.split(" ")[0]
    except:
        d = 120
    return int(d)

def get_cons_str(s,max_l):
    if len(s) > max_l:
        return s[:max_l-4]+"..."
    else:
        return s

def parse_json(file_path=None,j=None):
    if file_path is not None:
        j = json.load(open(file_path,"r",encoding="utf-8"))
    
    try:
        id = j["id"]
    except:
        print(f"Error processing {file_path}, file has no id.")
        os.remove(file_path)
        return 
    
    if id is None:
        id = j["code"]
        
    try:
        rate, rater = get_rate(j["meta"]["評分"])
    except:
        rate = 0
        rater = 0
        
    try:
        duraion = get_duration(j["meta"]["時長"])
    except:
        duraion = 120
        
    try:
        released = j["meta"]["日期"]
    except:
        released = "2020-01-01"
    
    defualt_video_path = j.setdefault("video_path","")
    

    movie,created = Movie.objects.get_or_create(id=id,
                        defaults={
                        "code": j["code"],
                        "current_title": get_cons_str(j["current-title"],400),
                        "origin_title": get_cons_str(j["origin-title"],400),
                        "release_date": released,
                        "duration": duraion,
                        "rate": rate, 
                        "rater": rater,
                        "video_src": j.setdefault("video_src",""),
                        "cover": j["cover"],
                        "video_path": defualt_video_path,
                        "processed": j.setdefault("processed",False),
                        "local": defualt_video_path != "" and os.path.exists(defualt_video_path),
                        })
    
    if created == False and movie.in_database == True:
        return 
    
        # movie = Movie(**movie_info)
    try:
        p = j["meta"]["發行"][0]
        pub, created = Group.objects.get_or_create(id=p[1],
                        defaults={
                        'name': p[0],
                        'role': "publisher",
                        'avatar': ""
                    })
        if created:
            pub.save()
        movie.publisher = pub
    except:
        pass
    
    try:
        d = j["meta"]["導演"][0]

        director, created = Group.objects.get_or_create(id=d[1],
                            defaults={
                        'name': d[0],
                        'role': "director",
                        'avatar': ""
                    })
        
        if created:
            director.save()
        movie.director = director
    except:
        pass
    
    try:
        s = j["meta"]["系列"]
        
        series,created = Group.objects.get_or_create(id=s[1],
                        defaults={
                        'name': s[0],
                        'role': "series",
                        'avatar': ""
                    }
                        )
        if created:
            series.save()
        movie.series = series
    except:
        pass
    
    try:
        m = j["meta"]["片商"][0]
        
        maker,created = Group.objects.get_or_create(id=m[1],
                        defaults={
                        'name': m[0],
                        'role': "maker",
                        'avatar': ""
                    })

        if created:
            maker.save()
        movie.maker = maker
    except:
        pass
    
    try:
        tags = j["meta"]["類別"]
        for tag in tags:
            
            t, created = Group.objects.get_or_create(id=tag[1],
                        defaults={
                            'name': tag[0],
                            'role': "tag",
                            'avatar': ""
                        })
            if created:
                t.save()
            movie.tags.add(t)
    except:
        pass
    
    try:
        actors = j["meta"]["演員"]
        for actor in actors:
            a, created = Group.objects.get_or_create(id=actor[1],
                        defaults={
                            'name': actor[0],
                            'role': "actor",
                            'avatar': ""
                        })
        
            if created:
                a.save()
            movie.actors.add(a)
    except:
        pass
    
    try:
        rs = j["related"]
        for r in rs:
            
            related, created = Movie.objects.get_or_create(id=r["href"],
                    defaults={
                        'code': r["code"],
                        'current_title': r["title"],
                        'origin_title': "",
                        'release_date': "2020-01-01",
                        'duration': 120,
                        'rate': 0,
                        'rater': 0,
                        'video_src': "",
                        'cover': r["img"],
                        'video_path': "",
                        'processed': False,
                        'local': False
                    })

            if created:
                related.save()
            movie.related.add(related)
            
    except:
        pass 
    
    try:
        ml = j["may_like"]
        for m in ml:
            may_like, created = Movie.objects.get_or_create(id=m["href"],
                    defaults= {
                        "code": m["code"],
                        "current_title": m["title"],
                        "origin_title": "",
                        "release_date": "2020-01-01",
                        "duration": 120,
                        "rate": 0,
                        "rater": 0,
                        "video_src": "",
                        "cover": m["img"],
                        "video_path": "",
                        "processed": False,
                        "local": False
                    })

            if created:
                may_like.save()

            movie.may_like.add(may_like)
    except Exception as e:
        print(f"Error processing may_like movies: {e}")
    movie.in_database = True 
    movie.save()
        
    try:
        magnets = j["magnets"]
        for magnet in magnets:
            m,created = Magnet.objects.get_or_create(id=magnet["href"],
                            defaults={
                                'name': magnet["name"],
                                'movie': movie,
                                'meta': magnet["meta"],
                                'tags': str(magnet["tags"]),
                                'time': magnet["time"]
                            }
                            )
            m.save()
    except:
        pass 
    
def parser_all_json(folder):
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".json"):
                print(f"Processing {file}")
                parse_json(os.path.join(root, file))
    
    
if __name__ == '__main__':
    # parse_json(r"\\10.16.12.105\disk\G\Info\A\ABP\ABP-656\ABP-656.json")
    parser_all_json(r"\\10.16.12.105\disk\G\Info")
    
    