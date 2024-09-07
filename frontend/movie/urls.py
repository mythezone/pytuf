from django.contrib import admin
from django.urls import path

from . import views 
from person import views as p_views

urlpatterns = [
    path("",views.index, name="index"),
    path("id/<str:movie_id>",views.detail, name="detail"),
    path("code/<str:movie_code>",views.code_detail, name="code_detail"),
]