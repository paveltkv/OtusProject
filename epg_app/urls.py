from django.urls import path

import epg_app.views as epg_app

app_name = 'epg_app'

urlpatterns = [
    path('init/', epg_app.init_epg, name='init_epg'),

    path('<int:epg_channel_id>/programmes/', epg_app.epg_item_programmes, name='epg_item_programmes'),

    path('download/', epg_app.download_epg, name='download_epg'),
    path('<int:pk>/load/', epg_app.load_epg, name='load_epg'),

    path('<int:pk>/detail/', epg_app.EpgDetailView.as_view(), name='epg_detail'),
    path('add/', epg_app.EpgAddView.as_view(), name='add_epg'),
    path('<int:pk>/edit/', epg_app.EpgEditView.as_view(), name='edit_epg'),
    path('<int:pk>/delete/', epg_app.EpgDeleteView.as_view(), name='delete_epg'),
]
