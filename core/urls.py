from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
path('change-password/', views.change_password, name='change_password'),
]
