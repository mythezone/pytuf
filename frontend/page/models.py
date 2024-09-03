from django.db import models

# Create your models here.
class Page(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=500)
    title = models.CharField(max_length=100)
    tp = models.ForeignKey('PageType', on_delete=models.CASCADE)
    intro = models.TextField()
    
    def __str__(self):
        return self.title
    
class PageType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.tp
    
