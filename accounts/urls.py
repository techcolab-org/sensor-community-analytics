from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ... your other URL patterns ...
    path('change-password/', views.change_password, name='change_password'),
]