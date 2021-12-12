from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.create_score, name='create_score'),
    path('score/<int:pk>', views.score_detail, name='score_detail'),
    path('user/<int:pk>', views.user_detail, name='user_detail'),
    path('search/', views.search, name='search'),
    path('score/<int:pk>/like/', views.like, name='like'), #'score/<int:pk>/like/'とすることでユニークとなる
    path('likeC/', views.likeC, name='likeC'),
    path('comment/<int:pk>', views.comment, name='comment'),
    path('user_edit/<int:pk>', views.user_edit, name='user_edit'),
    path('score_edit/<int:pk>', views.score_edit, name='score_edit'),
    path('albam_sort/<int:pk>', views.albam_sort, name='albam_sort'),
    path('albam_edit/<int:pk>', views.albam_edit, name='albam_edit'),
    path('user_likes/<int:pk>', views.user_likes, name='user_likes'),
    path('follow/<int:pk>', views.follow, name='follow'),
    path('user_follows/<int:pk>', views.user_follows, name='user_follows'),
    path('albam_detail/<int:pk>', views.albam_detail, name='albam_detail'),
    path('user_explanation/<int:pk>', views.user_explanation, name='user_explanation'),
    path('profit/<int:pk>', views.profit, name='profit'),
    path('stripe_created/<int:pk>', views.stripe_created, name='stripe_created'),
    path('base_notice/', views.base_notice, name='base_notice'),
    path('notice_detail/<int:pk>', views.notice_detail, name='notice_detail'),
    path('notice/<int:pk>', views.notice, name='notice'),
    path('score_delete/<int:pk>', views.score_delete, name='score_delete'),
    path('albam_delete/<int:pk>', views.albam_delete, name='albam_delete'),
] 