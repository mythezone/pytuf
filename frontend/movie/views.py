from django.shortcuts import render
from .models import Movie, Magnet

# Create your views here.
def index(request):
    
    return render(request, 'index.html')

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