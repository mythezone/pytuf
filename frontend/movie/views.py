from django.shortcuts import render
from .models import Movie, Magnet
from django.core.paginator import Paginator
import shutil, pathlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json 
import urllib.parse
import os 
from tools.qbdown import QBTorrentDownloader

# Create your views here.
qbt= {
        "url": "http://10.16.51.226:8080",
        "username": "mythezone",
        "password": "19891016Zmy!"
    }

ALL_MOVIES = Movie.objects.exclude(video_path="")
QBT = QBTorrentDownloader(qb_url=qbt['url'], username=qbt['username'], password=qbt['password'])


def local_video(request):
    local = request.GET.get('local', '1')
    if local == '1':
        all_movies = Movie.objects.exclude(video_path="").order_by('-id')
    else:
        all_movies = Movie.objects.all().order_by('-id')
    # print("all movie num:", len(all_movies))
    paginator = Paginator(all_movies, 12)
    page_num = request.GET.get('page', 1)
    
    page_obj = paginator.get_page(page_num)


    return render(request, 'index.html', {"page_obj": page_obj,"title":"所有电影","total":len(all_movies)})

def random_movies(request):
    random_movies = ALL_MOVIES.order_by('?')[:12]
    paginator = Paginator(random_movies, 12)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    return render(request, 'index.html', {"page_obj": page_obj,"random":True,"title":"运气不错",'total':12})

def my_top(request):
    num = request.GET.get('num', '100')
    num = int(num)
    top = ALL_MOVIES.order_by('-my_rate')[:num]
    paginator = Paginator(top, 12)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    return render(request, 'index.html', {"page_obj": page_obj,"title":"我的最佳", 'total':num})

def viewer_top(request):
    num = request.GET.get('num', '100')
    num = int(num)
    top = ALL_MOVIES.order_by('-rate')[:num]
    paginator = Paginator(top, 12)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    return render(request, 'index.html', {"page_obj": page_obj,"title":"观众最佳","total":num})

def recent(request):
    num = request.GET.get('num', '12')
    num = int(num)
    recent_movies = ALL_MOVIES.order_by('-release_date')[:num]
    paginator = Paginator(recent_movies, 12)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    return render(request, 'index.html', {"page_obj": page_obj,"title":"最新发布","total":num})
    

def all(request):
    all_movies = Movie.objects.all().order_by('-id')
    print("all movie num:", len(all_movies))
    paginator = Paginator(all_movies, 12)
    page_num = request.GET.get('page', 1)
    
    page_obj = paginator.get_page(page_num)


    return render(request, 'index.html', {"page_obj": page_obj})

def detail(request, movie_id):
    
    try:
        movie = Movie.objects.get(id=movie_id)
    except:
        movie = None 
        
    if movie :
        return render(request, 'detail.html', {"movie": movie})
    
    else:
        return render(request, '404.html')
    
def code_detail(request, movie_code):
    
    try:
        movie = Movie.objects.get(code=movie_code)
    except:
        movie = None 
        
    if movie :
        magnets = Magnet.objects.filter(movie=movie)
        return render(request, 'detail.html', {"movie": movie,"magnets":magnets})
    
    else:
        return render(request, '404.html')


# @csrf_exempt
# def del_movie(request, movie_id):
#     if request.method == 'POST':
#         try:
#             decoded_movie_id = movie_id.replace('_', '/')
#             movie = Movie.objects.get(id=decoded_movie_id)
#             movie_path = movie.video_path
#             parent = pathlib.Path(movie_path).parent
#             shutil.rmtree(parent)
#             movie.delete()
#             return JsonResponse({'success': True})
#         except Movie.DoesNotExist:
#             return JsonResponse({'success': False, 'error': 'Movie not found'})
#     return JsonResponse({'success': False, 'error': 'Invalid request method'})
           
@csrf_exempt
def del_movie(request, movie_id):
    if request.method == 'POST':
        try:
            decoded_movie_id = movie_id.replace('_', '/')
            movie = Movie.objects.get(id=decoded_movie_id)
            movie_path = movie.video_path
            # 将路径转换为标准的文件系统路径
            movie_path = movie_path.replace('file://', '')
            parent = pathlib.Path(movie_path).parent
            # 修改文件和目录权限

            shutil.rmtree(parent)
            movie.rate = -1 
            movie.video_path = ""
            movie.save()
            return JsonResponse({'success': True})
        except Movie.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Movie not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

           
@csrf_exempt
def rate_movie(request, movie_id):
    if request.method == 'POST':
        try:
            decoded_movie_id = movie_id.replace('_', '/')
            movie = Movie.objects.get(id=decoded_movie_id)
            data = json.loads(request.body)
            rating = data.get('rating')
            if rating is not None:
                movie.my_rate = float(rating)
                movie.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid rating'})
        except Movie.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Movie not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def update_comment(request, movie_id):
    if request.method == 'POST':
        try:
            decoded_movie_id = movie_id.replace('_', '/')
            movie = Movie.objects.get(id=decoded_movie_id)
            data = json.loads(request.body)
            comment = data.get('comment')
            if comment is not None:
                movie.comment = comment
                movie.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid comment'})
        except Movie.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Movie not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_magnets(request, movie_id):
    try:
        decoded_movie_id = movie_id.replace('_', '/')
        movie = Movie.objects.get(id=decoded_movie_id)
        magnets = Magnet.objects.filter(movie=movie)
        return JsonResponse({'success': True, 'magnets': [{'id':magnet.id,'name': magnet.name, 'meta': magnet.meta, 'tags': magnet.tags, 'time': magnet.time} for magnet in magnets]})
    except Movie.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Movie not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@csrf_exempt
def download_magnet(request, magnet_id):
    # magnet:?xt=urn:btih:0121bfbfb9a162ad3aac26f4ff42a71570d1ed6e&=[javdb.com]
    magnet_id = "magnet:?xt=urn:btih:"+magnet_id+"&=[javdb.com]"
    print(magnet_id)
    if request.method == 'POST':
        try:
            print(magnet_id)
            QBT.download(magnet_id, "from_web")
            return JsonResponse({'success': True})
        except Magnet.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Magnet not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})