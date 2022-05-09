from django.contrib.auth.models import AbstractUser

from django.db import models
from epg_app.models import Epg


class CustomUser(AbstractUser):
    playlist_rules = models.TextField(blank=True)
    generated_playlist = models.TextField(blank=True)
    generated_epg = models.TextField(blank=True)
    api_key = models.CharField(max_length=128, blank=True)
    icons_source = models.ForeignKey(Epg, on_delete=models.SET_NULL, blank=True, null=True)
