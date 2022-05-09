from django.contrib import admin

from .models import Epg, EpgChannel, EpgProgramme

admin.site.register(Epg)
admin.site.register(EpgChannel)
admin.site.register(EpgProgramme)
