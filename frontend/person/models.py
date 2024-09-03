from django.db import models
import enum

# Create your models here.
class People(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    role = models.ForeignKey("PeopleType", on_delete=models.CASCADE, related_name="people")
    avatar = models.CharField(max_length=200)
    intro = models.TextField()
    urls = models.ManyToManyField("page.Page", related_name="people")

    def __str__(self) -> str:
        return self.role+"-"+self.name
    
class PeopleType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
