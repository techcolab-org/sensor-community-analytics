from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    # path('', views.home, name='home'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]
