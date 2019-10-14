from django.conf.urls import url
from accounts import views
from django.urls import path
from feed import views
app_name = 'feed'

urlpatterns = [
    url(r'^profile/$', views.view_profile, name='profile_info'),
    path('profile/<slug:profile_username>/', views.view_profile, name='profile_info'),
    url(r'^feed/$', views.feed, name='news_feed'),

    url(r'^find_friends/$', views.find_friends, name='find_friends'),
    url(r'^connect/$', views.send_friend_request, name='send_friend_request'),
    url(r'^friends/$', views.friends_list, name='friends_list'),

    url(r'^sent_friends_requests/$', views.sent_friend_requests, name='sent_friend_requests_list'),
    url(r'^pending_friends_requests/$', views.pending_friend_requests, name='pending_friend_requests_list'),

    url(r'^accept_request/$', views.accept_friend_request, name='accept_friend_request'),
    url(r'^decline_request/$', views.decline_friend_request, name='decline_friend_request'),
    
]