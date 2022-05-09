"""aggregator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

import epg_app.views as epg_app

urlpatterns = [
    path('', epg_app.index, name='main'),

    path('epg_sources/', epg_app.epg_sources, name='epg_sources'),
    path('programmes/<int:epg_channel_id>/', epg_app.programmes, name='programmes'),
    path('channels/', epg_app.epg_channels, name='epg_channels'),
    path('channels/epg:<int:pk>/', epg_app.epg_channels, name='epg_channels'),

    path('epg/', include('epg_app.urls', namespace='epg')),
    path('playlist/', include('playlist_app.urls', namespace='playlist')),
    path('user/', include('user_app.urls', namespace='user')),


    path('admin/', admin.site.urls),
]
