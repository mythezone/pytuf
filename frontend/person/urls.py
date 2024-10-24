from django.contrib import admin
from django.urls import path

from . import views 

urlpatterns = [
    path("<str:group_id>",views.group, name="group"),
]