from django import forms
from django.forms import ModelForm
from .models import Albam, Follow, Score, Comment, Song_heart, Comment_heart, Follow
from accounts.forms import CustomUser

class AlbamForm(forms.ModelForm):
    class Meta:
        model = Albam
        fields = ('albam_title', 'art')

AlbamFormSet = forms.modelformset_factory(Albam, form = AlbamForm, extra = 0, max_num = 1)

class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ('song_name', 'musicfile', 'midifile', 'explanation', 'score_art', 'price', 'albam_num')

ScoreFormSet = forms.modelformset_factory(Score, form = ScoreForm, extra = 0, can_delete=True)
TagsInlineFormSet = forms.inlineformset_factory(
    Score, Score.tags.through, fields='__all__', can_delete=False
)

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('face','username','explanation')

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content', )

class SongHeartForm(ModelForm):
    class Meta:
        model = Song_heart
        exclude = ('user','song')

class CommentHeartForm(ModelForm):
    class Meta:
        model = Comment_heart
        exclude = ('user','comment')

class FollowForm(ModelForm):
    class Meta:
        model = Follow
        exclude = ('user','follow')

