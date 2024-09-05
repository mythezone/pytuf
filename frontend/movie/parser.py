
from pprint import pprint
# Insert the path into sys.path for importing.
import sys
import os
import json 

sys.path.append(r"C:\Users\mythezone\project\github\pytuf\frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend.settings')
import django  
django.setup()

from movie.models import Movie
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

def parse_json(file_path):
    j = json.load(open(file_path,"r",encoding="utf-8"))
    rate, rater = get_rate(j["meta"]["評分"])
    duraion = get_duration(j["meta"]["時長"])
    movie_info = {
        "id": j["id"],
        "code": j["code"],
        "current_title": j["current-title"],
        "origin_title": j["origin-title"],
        "release_date": j["meta"]["日期"],
        "duration": duraion,
        "rate": rate, 
        "rater": rater,
        "video_src": j["video_src"],
        "cover": j["cover"],
        "video_path": j["video_path"],
        "processed": j["processed"]
    }
    
    movie = Movie(**movie_info)
    movie.save()
    
    try:
        p = j["meta"]["發行"][0]
        pub = Group.objects.get(id=p[1])
        if pub is None:
            pub = Group(id=p[1], name=p[0], role="publisher", avatar="")
            pub.save()
        movie.publisher = pub
    except:
        pass
    
    try:
        d = j["meta"]["導演"][0]
        director = Group.objects.get(id=d[1])
        if director is None:
            director = Group(id=d[1], name=d[0], role="director", avatar="")
            director.save()
        movie.director = director
    except:
        pass
    
    try:
        s = j["meta"]["系列"]
        series = Group.objects.get(id=s[1])
        if series is None:
            series = Group(id=s[1], name=s[0], role="series", avatar="")
            series.save()
        movie.series = series
    except:
        pass
    
    try:
        m = j["meta"]["片商"][0]
        maker = Group.objects.get(id=m[1])
        if maker is None:
            maker = Group(id=m[1], name=m[0], role="maker", avatar="")
            maker.save()
        movie.maker = maker
    except:
        pass
    
    try:
        tags = j["meta"]["類別"]
        for tag in tags:
            t = Group.objects.get(id=tag[1])
            if t is None:
                t = Group(id=tag[1], name=tag[0], role="tag", avatar="")
                t.save()
            movie.tags.add(t)
    except:
        pass
    
    try:
        actors = j["meta"]["演員"]
        for actor in actors:
            a = Group.objects.get(id=actor[1])
            if a is None:
                a = Group(id=actor[1], name=actor[0], role="actor", avatar="")
                a.save()
            movie.actors.add(a)
    except:
        pass
    
    try:
        rs = j["related"]
        for r in rs:
            related = Movie.objects.get(id=r["href"])
            if related is None:
                related = Movie(id=r["href"], code=r[], current_title="", origin_title="", release_date="2020-01-01", duration=120, rate=0, rater=0, video_src="", cover="", video_path="", processed=False)
                related.save()
                
            movie.related.add(related)
        
        
    

    
if __name__ == '__main__':
    parse_json(r"\\10.16.12.105\disk\G\Info\A\ABP\ABP-656\ABP-656.json")
    
    