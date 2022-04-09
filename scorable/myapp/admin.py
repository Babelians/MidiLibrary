from django.contrib import admin
from .models import Albam, Score, Comment, Score_buying_history, Song_heart, Comment_heart, Follow, Tag, Notice
from .forms import ScoreFormSet

admin.site.register(Score)
admin.site.register(Albam)
admin.site.register(Comment)
admin.site.register(Score_buying_history)
admin.site.register(Tag)
admin.site.register(Notice)
