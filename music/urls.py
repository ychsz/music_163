from django.urls import path
from . import views
app_name='music'
urlpatterns=[
    path('',views.song_list,name='song_list'),
    path('song/<str:song_id>',views.song_detail,name='song_detail'),
    path('artists/',views.artist_list,name='artist_list'),
    path('artist/<str:artist_id>/',views.artist_detail,name='artist_detail'),
    path('search/',views.search,name='search'),
    path('comment/<int:comment_id>/delete/',views.delete_comment,name='delete_comment'),
]