from django.contrib import admin
from django.urls import path

from . import views 
from person import views as p_views

urlpatterns = [
    path("",views.local_video, name="local"),
    path("all",views.all, name="all"),
    path('rate_movie/<str:movie_id>/', views.rate_movie, name='rate_movie'),
    path("id/<str:movie_id>",views.detail, name="detail"),
    path("code/<str:movie_code>",views.code_detail, name="code_detail"),
    path('update_comment/<str:movie_id>/', views.update_comment, name='update_comment'),
    path('del_movie/<str:movie_id>/', views.del_movie, name='del_movie'),
]