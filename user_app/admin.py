from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user_app.models import CustomUser


class CustomUserAdmin(UserAdmin):
    pass


admin.site.register(CustomUser, CustomUserAdmin)
