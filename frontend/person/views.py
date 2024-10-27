from django.shortcuts import render
from movie.models import Movie
from django.core.paginator import Paginator
from .models import Group

# Create your views here.

# def index(request):
#     all_movies = Movie.objects.exclude(video_path="").order_by('-id')
#     print("all movie num:", len(all_movies))
#     paginator = Paginator(all_movies, 12)
#     page_num = request.GET.get('page', 1)
    
#     page_obj = paginator.get_page(page_num)


#     return render(request, 'index.html', {"page_obj": page_obj})

def group(request, group_id):
    decoded_group_id = group_id.replace('_', '/')
    decoded_group_id = decoded_group_id.replace('-', '=')
    decoded_group_id = decoded_group_id.replace('+','?')
    group = Group.objects.get(id=decoded_group_id)
    local = request.GET.get('local', '1')
    
    if group is None:
        return render(request, '404.html')
    g_name = ""
    if decoded_group_id[1]=='a':
        group_movies = Movie.objects.filter(actors=group)
        g_name = "演员:"+group.name
    elif decoded_group_id[1]=='d':
        group_movies = Movie.objects.filter(director=group)
        g_name = "导演:"+group.name
    elif decoded_group_id[1]=='p':
        group_movies = Movie.objects.filter(publisher=group)
        g_name = "出品:"+group.name
    elif decoded_group_id[1]=='m':
        group_movies = Movie.objects.filter(maker=group)
        g_name = "制作:"+group.name
    elif decoded_group_id[1]=='t':
        group_movies = Movie.objects.filter(tags=group)
        g_name = "标签:"+group.name
    
    if local == '1':
        group_movies = group_movies.exclude(video_path='').order_by('-id')
        
    total = len(group_movies)
        
    paginator = Paginator(group_movies, 12)
    page_num = request.GET.get('page', 1)
    
    page_obj = paginator.get_page(page_num)
    return render(request, 'group.html', {"page_obj": page_obj,"title":g_name, "total":total})
    
    
    
