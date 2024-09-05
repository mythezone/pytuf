from django.db import models
import datetime

# Create your models here.
class Movie(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    code = models.CharField(max_length=255,null=True,default="")
    current_title = models.CharField(max_length=255,null=True)
    origin_title = models.CharField(max_length=255,null=True)
    release_date = models.DateField(default=datetime.date.today)
    duration = models.IntegerField(default=120)
    rate = models.FloatField(default=0)
    rater = models.IntegerField(default=0)
    video_src =  models.CharField(max_length=500,default="")
    cover = models.CharField(max_length=500,default="")
    
    video_path = models.CharField(max_length=500, default="")
    processed = models.BooleanField(default=False)
    
    publisher = models.ForeignKey("person.Group", on_delete=models.SET_NULL, null=True, related_name="publish_movies")
    director = models.ForeignKey("person.Group", on_delete=models.SET_NULL, null=True, related_name="direct_movies")
    series = models.ForeignKey("person.Group", on_delete=models.SET_NULL, null=True, related_name="series_movies")
    maker = models.ForeignKey("person.Group", on_delete=models.SET_NULL, null=True, related_name="make_movies")
    
    tags = models.ManyToManyField("person.Group", related_name="tag_movies")
    actors = models.ManyToManyField("person.Group", related_name="act_movies")
    
    local = models.BooleanField(default=False)
    
    related = models.ManyToManyField("self", related_name="related_movies")
    may_like = models.ManyToManyField("self", related_name="may_like_movies")
    
    def __str__(self):
        return self.code + " : " +self.current_title
    
class Magnet(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255,default="")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="magnets")
    meta = models.CharField(max_length=255,default="")
    tags = models.CharField(max_length=255,default="")
    time = models.DateField(default=datetime.date.today)
    
    def __str__(self):
        return self.name + " : " + self.meta