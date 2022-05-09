from django.contrib.auth.views import LoginView
from django.views.generic import CreateView

from user_app.forms import CustomUserCreateForm, UserLoginForm
from user_app.models import CustomUser


class CustomUserCreateView(CreateView):
    model = CustomUser
    success_url = '/'
    form_class = CustomUserCreateForm
    # fields = ('username', 'email', 'password1', 'password2')


class CustomUserLoginView(LoginView):
    model = CustomUser
    success_url = '/'
    form_class = UserLoginForm
    # fields = ('username', 'email', 'password1', 'password2')
