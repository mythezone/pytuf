from django.shortcuts import render
from .models import Movie, Magnet
from django.core.paginator import Paginator
import shutil, pathlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json 
import urllib.parse
import os 
# Create your views here.
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


    return render(request, 'index.html', {"page_obj": page_obj,"total":len(all_movies)})

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
            movie.delete()
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