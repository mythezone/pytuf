from django.db import models

# Create your models here.
class Movie(models.Model):

    code = models.CharField(max_length=255)
    published_date = models.DateField()
    duration_min = models.IntegerField()
    location = models.CharField(max_length=255)
    info = models.JSONField() # title, cover, screenshots, description, preview, magnet, comment, related, etc.
    
    director = models.ForeignKey('person.People', on_delete=models.CASCADE, related_name='directors')
    studio = models.ForeignKey('person.People',  on_delete=models.CASCADE, related_name='studios')
    publisher = models.ForeignKey('person.People', on_delete=models.CASCADE,  related_name='publishers')
    series = models.ForeignKey('person.People',  on_delete=models.CASCADE, related_name='series')
    actors = models.ManyToManyField('person.People',  related_name='actors')
    tags = models.ManyToManyField('person.People',  related_name='tags')
    
    rating = models.FloatField(default=0)
    parsed = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    
    def __str__(self):
        return self.code
    