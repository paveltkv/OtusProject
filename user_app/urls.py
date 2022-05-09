from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

import user_app.views as user_app

app_name = 'user_app'

urlpatterns = [
    path('register/', user_app.CustomUserCreateView.as_view(), name='register'),
    path('login/', user_app.CustomUserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
