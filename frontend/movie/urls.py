from django.contrib import admin
from django.urls import path

from . import views 
from person import views as p_views

urlpatterns = [
    path("",views.local_video, name="local"),
    path("all",views.all, name="all"),
    path('random/', views.random_movies, name='random'),
    path('top/', views.my_top, name='top'),
    path('ctop/', views.viewer_top, name='ctop'),
    path('recent/', views.recent, name='recent'),
    path('rate_movie/<str:movie_id>/', views.rate_movie, name='rate_movie'),
    path("id/<str:movie_id>",views.detail, name="detail"),
    path("code/<str:movie_code>",views.code_detail, name="code_detail"),
    path('update_comment/<str:movie_id>/', views.update_comment, name='update_comment'),
    path('del_movie/<str:movie_id>/', views.del_movie, name='del_movie'),
    path('magnets/<str:movie_id>/', views.get_magnets, name='magnets'),
    path('download/<str:magnet_id>/', views.download_magnet, name='download'),
    path('search/', views.search_result, name='search'),
]