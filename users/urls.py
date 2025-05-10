#users/urls.py
from django.urls import path
from .views import (
    CustomRegisterView,
    CustomLoginView,
    CustomLogoutView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    ProfileView,
    GoogleLogin,
    FacebookLogin,
    AppleLogin
)

app_name = 'users'

urlpatterns = [
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset_confirm/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('google/',    GoogleLogin.as_view(),    name='google_login'),
    path('facebook/',  FacebookLogin.as_view(),  name='facebook_login'),
   # path('microsoft/', MicrosoftLogin.as_view(), name='microsoft_login'),
    path('apple/',     AppleLogin.as_view(),     name='apple_login'),

]