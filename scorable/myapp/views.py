from django.conf import settings
from django.db.models.fields import NullBooleanField
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from stripe.api_resources import source
from .models import Albam, Score, Comment, Score_buying_history, Song_heart, Comment_heart, Follow, Tag
from .forms import AlbamForm, ScoreForm, ScoreFormSet, TagsInlineFormSet, UserEditForm, CommentForm, SongHeartForm, CommentHeartForm, FollowForm
from accounts.models import CustomUser
from accounts.forms import CustomUser
from scorable.settings import FRONTEND_URL, MEDIA_ROOT
import os
import copy #リストの参照無しコピー
from django.db.models import Q
import itertools #リストの１次元化 

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

range_10 = [i for i in range(10)]
range_100 = [i for i in range(100)]

def index(request):
    if request.user.id:
        user = CustomUser.objects.get(pk=request.user.id)
        follow_scores = search_byFollow(user)[:6]
        recommend_scores = search_byLike_fromTag(user)[:10]
    else:
        user = False
        follow_scores = False
        recommend_scores = False
    tags = Tag.objects.order_by('-num')[:20]
    scores_tag = dict()
    for tag in tags:
        scores_tag[tag] = Score.objects.filter(tags=tag).order_by('uploaded_at')[:12]
    return render(request, 'myapp/index.html', {'tags':tags, 'scores_tag':scores_tag, 'follow_scores':follow_scores, 'recommend_scores':recommend_scores,})

def search(request):
    keyword = request.GET['keyword']
    keywords = keyword.split()
    artists = CustomUser.objects.order_by('-subscriber')
    scores = Score.objects.all().order_by('-play_count')
    flug = False
    for key in keywords:
        if key:
            flug = True
            scores = scores.filter(
            Q(song_name__icontains=key)|
            Q(artist_id__username__icontains=key)|
            Q(tags__name__icontains=key)
            ).order_by('-play_count').distinct() #重複削除
    if flug == False:
        scores = []
    score_dict = dict()
    for score in scores:
        score_dict[score] = score_to_tagsName(score)
    return render(request, 'myapp/search.html', {'artists':artists, 'score_dict':score_dict, 'keyword': keyword,'range_10': range_10 })

def user_detail(request, pk):
    posts = Score.objects.filter(artist_id=pk).order_by('-uploaded_at')
    my = CustomUser.objects.get(pk=pk)
    if request.user.id: #ログインしてるか
        follow_mycount = Follow.objects.filter(follow_id=pk, user_id=request.user).count()
    else:
        follow_mycount = 666
    return render(request, 'myapp/user_detail.html', {'posts': posts, 'my': my, 'followMyCount':follow_mycount,})

def albam_sort(request, pk):
    albams = Albam.objects.filter(artist_id=pk).order_by('-uploaded_at')
    albam_dict = dict()
    for albam in albams:
        albam_dict[albam] = Score.objects.filter(albam=albam).order_by('albam_num')
    my = CustomUser.objects.get(pk=pk)

    if request.user.id: #ログインしてるか
        follow_mycount = Follow.objects.filter(follow_id=pk, user_id=request.user).count()
    else:
        follow_mycount = 666
    return render(request, 'myapp/albam_sort.html', {'albams': albam_dict, 'my': my, 'followMyCount': follow_mycount,})

def user_likes(request, pk):
    posts = Song_heart.objects.filter(user_id=pk).order_by('-uploaded_at')
    my = CustomUser.objects.get(pk=pk)
    if request.user.id: #ログインしてるか
        follow_mycount = Follow.objects.filter(follow_id=pk, user_id=request.user).count()
    else:
        follow_mycount = 666
    return render(request, 'myapp/user_likes.html', {'posts': posts, 'my': my, 'followMyCount': follow_mycount,})

def user_follows(request, pk):
    follows = Follow.objects.filter(user_id=pk).order_by('-uploaded_at')
    my = CustomUser.objects.get(pk=pk)
    if request.user.id: #ログインしてるか
        follow_mycount = Follow.objects.filter(follow_id=pk, user_id=request.user).count()
    else:
        follow_mycount = 666
    return render(request, 'myapp/user_follows.html', {'follows': follows, 'my': my, 'followMyCount': follow_mycount,})

def user_explanation(request, pk):
    my = CustomUser.objects.get(pk=pk)
    if request.user.id: #ログインしてるか
        follow_mycount = Follow.objects.filter(follow_id=pk, user_id=request.user).count()
    else:
        follow_mycount = 666
    return render(request, 'myapp/user_explanation.html', {'my': my, 'followMyCount':follow_mycount,})

def albam_detail(request, pk):
    albam = Albam.objects.get(id=pk)
    my = CustomUser.objects.get(pk=albam.artist_id)
    scores = Score.objects.filter(albam=albam).order_by('albam_num')
    return render(request, 'myapp/albam_detail.html', {'albam': albam, 'my': my, 'scores':scores,})

def profit(request, pk):
    my = get_object_or_404(CustomUser, pk=pk)
    posts = Score_buying_history.objects.filter(user_id=my.id)
    account= stripe.Account.retrieve(my.stripe_id)

    if request.user.id == my.id:
        if  not account.details_submitted:
            accountLink = stripe.AccountLink.create(
                account = account.id,
                refresh_url = FRONTEND_URL,
                return_url = FRONTEND_URL+"/profit/"+str(my.id),
                type = "account_onboarding",
            )
            return redirect(accountLink.url)
        else:
            return render(request, 'myapp/profit.html', {'my': my, 'stripeLink':stripe.Account.create_login_link(my.stripe_id).url, "posts":posts,})
    else:
        return render(request, 'myapp/none.html',{})

def stripe_created(request):
    return render(request, 'myapp/index.html', {'request':request})

def user_edit(request, pk):
    my = CustomUser.objects.get(pk=pk)
    path = os.path.join(MEDIA_ROOT, str(my.face))
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=my)
        if form.is_valid():
            form.save()
            my2 = CustomUser.objects.get(pk=pk)
            path2 = os.path.join(MEDIA_ROOT, str(my2.face))
            if (path != path2) and (path != os.path.join(MEDIA_ROOT, 'face/defo.jpg')): #pathに変更があり、前の画像がデフォルトでないとき
                os.remove(path)
            return redirect('user_detail', pk=pk)
    else:
        form = UserEditForm(instance=my)
    return render(request, 'myapp/user_edit.html', {'my': my, 'form':form})

def addTag_byScores(request, score, n, i):
    if 0 < n: #scoreにtagをrequest.POSTから追加する
        for j in range(10):
            if request.POST["form-"+str(i)+"-tag-"+str(j)]:
                try:
                    tag = Tag.objects.get(name=request.POST["form-"+str(i)+"-tag-"+str(j)])
                except:
                    tag = Tag.objects.create(name=request.POST["form-"+str(i)+"-tag-"+str(j)])
                score.tags.add(tag)
                tag.num += n
                tag.save()
    else: #いったんすべてのタグをscoreから消す
        tags = score.tags.all()
        for tag in tags:
            score.tags.remove(tag)
            tag.num += n
            tag.save()

def create_score(request):
    if request.method == 'POST':
        a_form = AlbamForm(request.POST, request.FILES)
        s_formset = ScoreFormSet(request.POST, request.FILES, queryset = Score.objects.none())
        if s_formset.is_valid():
            if a_form.is_valid():
                albam = a_form.save(commit=False)
                albam.artist = request.user
                albam.save()
            else:
                albam = None
            scores = s_formset.save(commit=False)
            
            i = 0
            for score in scores:
                if albam:
                    score.albam = albam
                    if not score.score_art:
                        score.score_art = albam.art
                else:
                    if not score.score_art:
                        score.score_art = request.user.face
                score.artist = request.user
                score.save()

                addTag_byScores(request, score, 1, i)
                i += 1
            return redirect('score_detail', pk=score.pk)
    else:
        a_form = AlbamForm()
        s_formset = ScoreFormSet(queryset = Score.objects.none())
        if request.user.country == "JP":
            currency = '円'
        else:
            currency = 'usd'
    return render(request, 'myapp/create_score.html', {'a_form': a_form, 's_formset':s_formset, 'currency':currency})

#可変長16進数を2進数str変換
def vlen(hoge, i):
    if i == 16:
        hoge = int(hoge, 16)
        hoge2 = ''
        for i in range(7):
            if hoge % 2 == 1:
                hoge2 += '1'
                hoge = (hoge-1)/2
            else:
                hoge2 += '0'
                hoge /= 2
        fin = hoge2[::-1]
    return fin
            
            
def score_to_tagsName(score):
    tags = score.tags.all()
    tags_name = list()
    for tag in tags:
        tags_name.append(tag.name)
    return tags_name

def search_byFollow(user):
    following = Follow.objects.filter(user=user)
    scores = list()
    for f in following:
        scores.append(Score.objects.filter(artist=f.follow))
    scores = list(itertools.chain.from_iterable(scores))
    return scores

def score_to_score_byTags(score):
    tags = score.tags.all()
    scores = list()
    for tag in tags:
        scores.append(Score.objects.filter(tags=tag))
    scores = list(itertools.chain.from_iterable(scores))
    scores = list(set(scores))
    return scores

def search_byLike_fromTag(user):
    likes = Song_heart.objects.filter(user=user)
    tags = list()
    for l in likes:
        tags.append(l.song.tags.all())
    tags = list(itertools.chain.from_iterable(tags))
    tags = list(set(tags))
    scores = list()
    for t in tags:
        scores.append(Score.objects.filter(tags=t))
    scores = list(itertools.chain.from_iterable(scores))
    scores = list(set(scores))
    return scores


def score_detail(request, pk):
    score = get_object_or_404(Score, pk=pk)
    score.play_count += 1
    score.save()
    recommend_scores = Score.objects.all().order_by('-play_count')
    recommend_byAlbam = Score.objects.filter(albam=score.albam, albam_num=score.albam_num+1)
    recommend_byTag = score_to_score_byTags(score)
    if request.user.id:
        purchased = Score_buying_history.objects.filter(score_id=score.id, user_id=request.user)
    else:
        purchased = False
    account = stripe.Account.retrieve(score.artist.stripe_id)

    if score.artist.country == "JP":
        currency = 'jpy'
    else:
        currency = 'usd'

    posts = Comment.objects.filter(song_id=pk).order_by('-heart_count')
    if request.user.id: #ログインしてるか
        song_heart = Song_heart.objects.filter(song_id=pk, user_id=request.user)
        song_heart_mycount = song_heart.count()
        follow_mycount = Follow.objects.filter(follow_id=score.artist.id, user_id=request.user).count()
        for post in posts:
            if Comment_heart.objects.filter(comment_id=post.id):
                post.my_heart = 1
            else:
                post.my_heart = 0
    else:
        song_heart_mycount = 666
        follow_mycount = 666
        for post in posts:
            post.my_heart = 0

    if request.method == 'POST':
        token = request.POST['stripeToken']  # フォームでのサブミット後に自動で作られる
        try:
            # 購入処理
            if account.details_submitted: #stripeのアカウントが作られているなら
                charge = stripe.Charge.create(
                    source=token,
                    amount=score.price,
                    application_fee_amount=int(score.price*0.1),
                    currency=currency,
                    description='メール:{} Midi:{}'.format(request.user.email, score.song_name),
                    transfer_data={
                        'destination': score.artist.stripe_id,
                    }
                )
            else:
                charge = stripe.Charge.create(
                    source=token,
                    amount=score.price,
                    currency=currency,
                    description='メール:{} Midi:{}'.format(request.user.email, score.song_name),
                )
                score_user = get_object_or_404(CustomUser, pk=score.artist.id)
                score_user.profit += score.price
                score_user.save()
        except stripe.error.CardError as e:
            return render(request,)
        else:
            Score_buying_history.objects.create(score=score, user=request.user, price=score.price, stripe_id=charge.id)

    path = os.path.join(MEDIA_ROOT, str(score.midifile))
    f = open(path,'rb')
    midhead = f.read(4).hex()
    mid_h_data = f.read(4).hex()
    mid_h_format = f.read(2).hex()
    mid_h_track = int(f.read(2).hex(),16) #トラック数 (0埋め削除&10進数変換)
    mid_h_time = int(f.read(2).hex(), 16) #時間方式
    midtrack = [] #トラックチャンク始まり宣言
    mid_t_data = [] #データ長 (0埋め削除&10進数変換)
    mid_t_selection = [] #演奏データ
    mid_t_note = []
    mid_t_marker = []
    mid_t_tempo = []
    mid_t_rhythm = []
    mid_t_maxdt = 0

    for i in range(mid_h_track):
        midtrack.append(f.read(4).hex())
        mid_t_data.append(int(f.read(4).hex(),16))
        mid_t_note.append([])
        mid_t_marker.append([])
        mid_t_dtime = 0

        j = 0
        #mid_t_selection.append(f.read(mid_t_data[i]).hex())
        flag = True
        while(flag):
            hoge = f.read(1).hex()
            if int(hoge, 16)>128:
                dtime = vlen(hoge, 16)
                flag2 = True
                while(flag2):
                    hoge = f.read(1).hex()
                    if int(hoge, 16) < 128:
                        flag2 = False
                    dtime += vlen(hoge, 16)
                mid_t_dtime += int(dtime, 2)
            else:
                mid_t_dtime += int(hoge, 16)
                
            hoge = f.read(1).hex()
            #ランニングステータス判定
            #if 64 > int(hoge, 16) or (int(hoge, 16) >= 128 and 192 > int(hoge, 16)):
                #hoge = 90
            if hoge == 'ff':
                hoge2 = f.read(1).hex()
                if hoge2 == '51':
                    mid_t_tempo.append([])
                    mid_t_tempo[len(mid_t_tempo)-1].append(mid_t_dtime)
                    mid_t_tempo[len(mid_t_tempo)-1].append(int(f.read(int(f.read(1).hex(), 16)).hex(), 16))
                elif hoge2 == '58':
                    mid_t_rhythm.append([])
                    mid_t_rhythm[len(mid_t_rhythm)-1].append(mid_t_dtime)
                    mid_t_rhythm[len(mid_t_rhythm)-1].append(int(f.read(int(f.read(1).hex(), 16)).hex(), 16))
                elif hoge2 == '2f':
                    if f.read(1).hex() == '00':
                        flag = False
                elif hoge2 == '03':
                    mid_t_marker[i] = f.read(int(f.read(1).hex(), 16)).hex()
                else:
                    hoge2 = f.read(int(f.read(1).hex(), 16)).hex()
            elif hoge == ('80'or'81'or'82'or'83'or'84'or'85'or'86'or'87'or'88'or'89'or'8a'or'8b'or'8c'or'8d'or'8e'or'8f'):
                mid_t_note[i].append([])
                mid_t_note[i][len(mid_t_note[i])-1].append(mid_t_dtime)
                mid_t_note[i][len(mid_t_note[i])-1].append(int(f.read(1).hex(), 16))
                mid_t_note[i][len(mid_t_note[i])-1].append(f.read(1).hex())
                mid_t_note[i][len(mid_t_note[i])-1][2] = 0
                if mid_t_maxdt < mid_t_dtime:
                    mid_t_maxdt = mid_t_dtime
            elif hoge == ('90'or'91'or'92'or'93'or'94'or'95'or'96'or'97'or'98'or'99'or'9a'or'9b'or'9c'or'9d'or'9e'or'9f'):
                mid_t_note[i].append([])
                mid_t_note[i][len(mid_t_note[i])-1].append(mid_t_dtime)
                mid_t_note[i][len(mid_t_note[i])-1].append(int(f.read(1).hex(), 16))
                mid_t_note[i][len(mid_t_note[i])-1].append(int(f.read(1).hex(), 16))
                if mid_t_maxdt < mid_t_dtime:
                    mid_t_maxdt = mid_t_dtime
            elif hoge == ('c0'or'c1'or'c2'or'c3'or'c4'or'c5'or'c6'or'c7'or'c8'or'c9'or'ca'or'cb'or'cc'or'cd'or'ce'or'cf'): #プログラムチェンジとやら
                hoge = f.read(1).hex()
                if mid_t_maxdt < mid_t_dtime:
                    mid_t_maxdt = mid_t_dtime
            elif hoge == ('d0'or'd1'or'd2'or'd3'or'd4'or'd5'or'd6'or'd7'or'd8'or'd9'or'da'or'db'or'dc'or'dd'or'de'or'df'): #チャンネルプレッシャーとやら
                hoge = f.read(1).hex()
                if mid_t_maxdt < mid_t_dtime:
                    mid_t_maxdt = mid_t_dtime
            else:
                hoge = f.read(2).hex()
                #mid_t_selection.append(f.read(2).hex()) #不明なイベントは大体2バイト
            j += 1

    f.close()

    #===============================================
    #ミディの開始点と終端のデルタタイムを統合
    #===============================================
    note = []
    for i in range(len(mid_t_note)):
        note.append([])
        for j in range(len(mid_t_note[i])):
            for k in range(j+1, len(mid_t_note[i])):
                if mid_t_note[i][j][1] == mid_t_note[i][k][1] and mid_t_note[i][k][2] == 0:
                    mid_t_note[i][j].append(mid_t_note[i][k][0])
                    note[i].append(mid_t_note[i][j])
                    del mid_t_note[i][k] 
                    break

    return render(request, 'myapp/score_detail.html', {
        'score': score, 
        'score_art': score.score_art,
        'explanation': score.explanation,
        'midhead': midhead,
        'mid_h_data': mid_h_data,
        'mid_h_format': mid_h_format,
        'mid_h_track': mid_h_track,
        'mid_h_time': mid_h_time,
        'midtrack': midtrack,
        'mid_t_data': mid_t_data,
        'selection': mid_t_selection,
        'tempo': mid_t_tempo, #[0]:デルタタイム [1]:4分音符のマイクロ秒
        'rhythm': mid_t_rhythm,
        'note': note,
        'dtime': mid_t_dtime,
        'maxdt': mid_t_maxdt,
        'trackname': mid_t_marker, 
        'posts': posts,
        'songHeartMyCount': song_heart_mycount,
        'recommend_scores': recommend_scores,
        'recommend_byAlbam': recommend_byAlbam,
        'recommend_byTag': recommend_byTag,
        'public_key':settings.STRIPE_PUBLIC_KEY,
        'purchased':purchased,
        'followMyCount': follow_mycount,
        'currency': currency,
        'tags':score_to_tagsName(score),
    })

def like(request, pk): #いいね
    score = get_object_or_404(Score, pk=pk)

    if request.user.id: #ログインしてるか
        song_heart = Song_heart.objects.filter(song_id=pk, user_id=request.user)
        song_heart_mycount = song_heart.count()
    
        heart_form = SongHeartForm(request.POST)

        if heart_form.is_valid() and song_heart_mycount == 0:
            like = heart_form.save(commit=False)
            like.user = request.user
            like.song = score
            like.save()
            score.heart_count += 1
            score.save()
        elif heart_form.is_valid() and song_heart_mycount > 0:
            song_heart.delete()
            score.heart_count -= 1
            score.save()

        data = {

        }
        return JsonResponse(data)

def likeC(request):
    pk = int(request.POST.get('likeC_id'))
    if request.user.id: #ログインしてるか
        cheart_form = CommentHeartForm(request.POST)
        #cid = request.POST.get('LikeC', None)
        comment_idnum = Comment.objects.get(id=pk)
        comment_heart_this = Comment_heart.objects.filter(comment_id=pk)
        comment_heart_mycount = comment_heart_this.count()
        this_post = Comment.objects.get(id=pk)
        if cheart_form.is_valid() and comment_heart_mycount == 0:
            like = cheart_form.save(commit=False)
            like.user = request.user
            like.comment = comment_idnum
            like.save()
            this_post.heart_count += 1
            this_post.save()
        elif cheart_form.is_valid() and comment_heart_mycount > 0:
            comment_heart_this.delete()
            this_post.heart_count -= 1
            this_post.save()

        data = {

        }
        return JsonResponse(data)

def comment(request, pk):
    score = get_object_or_404(Score, pk=pk)
    if request.user.id: #ログインしてるか
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.owner = request.user
            comment.song = score
            comment.save()

    
        data = {

        }
        return JsonResponse(data)

def addTag_byScore(request, score, n):
    if 0 < n: #scoreにtagをrequest.POSTから追加する
        for j in range(10):
            if request.POST["form-tag-"+str(j)]:
                try:
                    tag = Tag.objects.get(name=request.POST["form-tag-"+str(j)])
                except:
                    tag = Tag.objects.create(name=request.POST["form-tag-"+str(j)])
                score.tags.add(tag)
                tag.num += n
                tag.save()
    else: #いったんすべてのタグをscoreから消す
        tags = score.tags.all()
        for tag in tags:
            score.tags.remove(tag)
            tag.num += n
            tag.save()

def score_edit(request, pk):
    score = Score.objects.get(pk=pk)

    if request.method == 'POST':
        addTag_byScore(request, score, -1)
        form = ScoreForm(request.POST, request.FILES, instance=score)
        if form.is_valid():
            form.save()
            addTag_byScore(request, score, 1)
        return redirect('user_detail', pk=request.user.pk)
    else:
        form = ScoreForm(instance=score)
        if request.user.country == "JP":
            currency = '円'
        else:
            currency = 'usd'

    if score.artist.id == request.user.id: #リクエストに不正があるか
        return render(request, 'myapp/score_edit.html',{
            'form': form,
            'score': score,
            'currency':currency,
            'tags':score_to_tagsName(score),
        })
    else:
        return render(request, 'myapp/none.html',{})


def albam_edit(request, pk):
    this_albam = Albam.objects.get(pk=pk)
    albam_scores = Score.objects.filter(albam=this_albam).order_by('albam_num')
    scores_num = albam_scores.count()
    scores_name = list()
    scores_midi = list()
    scores_explanation = list()
    scores_art = list()
    scores_music = list()
    scores_tag = list()
    scores_id = list()
    scores_price = list()
    for score in albam_scores:
        scores_name.append(score.song_name)
        scores_midi.append(score.midifile.url[16:])
        scores_explanation.append(score.explanation)
        scores_art.append(score.score_art.url)
        scores_music.append(score.musicfile.url[17:])
        scores_tag.append(score_to_tagsName(score))
        scores_id.append(score.id)
        scores_price.append(score.price)
    if request.method == 'POST':
        a_form = AlbamForm(request.POST, request.FILES, instance=this_albam)
        s_formset = ScoreFormSet(request.POST, request.FILES, queryset = Score.objects.filter(albam=this_albam).order_by('albam_num'))

        if s_formset.is_valid():
            if a_form.is_valid():
                albam = a_form.save(commit=False)
                albam.artist = request.user
                albam.save()
            else:
                albam = None

            scores = s_formset.save(commit=False)
            print(scores)
            print(albam_scores)
            i = 0
            for score in albam_scores:
                addTag_byScores(request, score, -1, i)
                i += 1
            
            i = 0
            for score in scores:
                if albam:
                    score.albam = albam
                    if not score.score_art:
                        score.score_art = albam.art
                else:
                    if not score.score_art:
                        score.score_art = request.user.face
                score.artist = request.user
                score.save()
                i += 1

            score_objects = list()
            print(s_formset.cleaned_data)
            for j in s_formset.cleaned_data:
                score_objects.append(j["id"])
            print(score_objects)

            albam_num_list = list()

            i = 0
            j = 0
            for score in score_objects:
                if score != None:
                    addTag_byScores(request, score, 1, i)
                else:
                    albam_num_list.append([])
                    albam_num_list[j].append(i)
                    albam_num_list[j].append(request.POST["form-"+str(i)+"-albam_num"])
                    j += 1
                i += 1

            for anl in albam_num_list:
                addTag_byScores(request, Score.objects.get(albam_num=anl[1]), 1, anl[0])

            return redirect('user_detail', pk=request.user.pk)
    else:
        a_form = AlbamForm(instance=this_albam)
        s_formset = ScoreFormSet(queryset = Score.objects.filter(albam=this_albam).order_by('albam_num'))
        if request.user.country == "JP":
            currency = '円'
        else:
            currency = 'usd'

    if this_albam.artist.id == request.user.id: #リクエストに不正があるか
        return render(request, 'myapp/albam_edit.html', {
            'a_form': a_form, 
            's_formset':s_formset,
            'albam': this_albam,
            'scores': albam_scores,
            'scores_num': scores_num,
            'scores_name': scores_name,
            'scores_midi': scores_midi,
            'scores_explanation':scores_explanation,
            'scores_art': scores_art,
            'scores_music': scores_music,
            'scores_tag': scores_tag,
            'scores_id': scores_id,
            'scores_price':scores_price,
            'currency': currency,
        })
    else:
        return render(request, 'myapp/none.html', {})

def follow(request, pk): #いいね
    followed_user = get_object_or_404(CustomUser, pk=pk)

    if request.user.id: #ログインしてるか
        follow = Follow.objects.filter(follow_id=pk, user_id=request.user)
        follow_mycount = follow.count()

    
        follow_form = FollowForm(request.POST)

        if follow_form.is_valid() and follow_mycount == 0:
            f = follow_form.save(commit=False)
            f.user = request.user
            f.follow = followed_user
            f.save()
            followed_user.subscriber += 1
            followed_user.save()
        elif follow_form.is_valid() and follow_mycount > 0:
            follow.delete()
            followed_user.subscriber -= 1
            followed_user.save()

        data = {

        }
        return JsonResponse(data)

