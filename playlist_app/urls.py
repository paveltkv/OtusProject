from django.urls import path

import playlist_app.views as playlist_app

app_name = 'playlist_app'

urlpatterns = [
    path('', playlist_app.index, name='playlist_main'),
    path('init/', playlist_app.init, name='init'),
    path('init_build_rules/', playlist_app.init_build_rules, name='init_build_rules'),
    path('change_api_key/', playlist_app.change_api_key, name='change_api_key'),
    path('download/', playlist_app.download, name='download'),
    path('<int:pk>/<str:api_key>.m3u8', playlist_app.user_playlist, name='user_playlist'),
    path('epg/<int:pk>.xml', playlist_app.user_epg, name='user_epg'),
    path('detail/<int:pk>/', playlist_app.PlayListDetailView.as_view(), name='playlist_detail'),
    path('create/', playlist_app.PlayListCreateView.as_view(), name='playlist_add'),
    path('update/<int:pk>/', playlist_app.PlayListUpdateView.as_view(), name='playlist_update'),
    path('delete/<int:pk>/', playlist_app.PlayListDeleteView.as_view(), name='playlist_delete'),
]
