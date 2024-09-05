from django.db import models
import enum

# Create your models here.
class Group(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=100,default="")
    role = models.CharField(max_length=20,default="tag")
    avatar = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.role+"-"+self.name
    
    
