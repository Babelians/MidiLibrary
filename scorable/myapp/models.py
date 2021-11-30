from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import CustomUser

class Albam(models.Model):
    artist = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, default=1)
    albam_title = models.CharField(max_length=50)
    art = models.ImageField(upload_to='albam_art/', blank=True, default='albam_art/defo.jpg')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Tag(models.Model):
    name = models.CharField(max_length=50)
    num = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Score(models.Model):
    albam = models.ForeignKey(Albam, on_delete=models.CASCADE, blank=True, null = True)
    albam_num = models.IntegerField(blank=True, null = True)
    song_name = models.CharField(max_length=50)
    artist = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    score_art = models.ImageField(upload_to='score_art/', blank=True, )#default='score_art/defo.png')
    musicfile = models.FileField(upload_to='musicfile/')
    midifile = models.FileField(upload_to='midifile/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    play_count = models.IntegerField(default=0)
    heart_count = models.IntegerField(default=0)
    explanation = models.CharField(max_length=3000, blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    price = models.IntegerField(default=0)

class Score_buying_history(models.Model):
    score = models.ForeignKey(Score, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    price = models.IntegerField(default=0)
    stripe_id = models.CharField(default="NULL",max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    content = models.TextField(max_length=2000)
    song =  models.ForeignKey(Score, on_delete=models.CASCADE,)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    heart_count = models.IntegerField(default=0)
    my_heart = models.IntegerField(default=0)

class Song_heart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    song =  models.ForeignKey(Score, on_delete=models.CASCADE,)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Comment_heart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    comment =  models.ForeignKey(Comment, on_delete=models.CASCADE,)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Follow(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='follow_user') #related_nameがどうこうでエラーだ出た
    follow =  models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    uploaded_at = models.DateTimeField(auto_now_add=True)




