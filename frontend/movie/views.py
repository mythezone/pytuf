from django.shortcuts import render
from .models import Movie, Magnet
from django.core.paginator import Paginator


# Create your views here.
def index(request):
    all_movies = Movie.objects.exclude(video_path="").order_by('-id')
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