from django.urls import path
from . import views

app_name = 'sensor'

urlpatterns = [
    path('', views.home, name='home'),
    path('station/add/', views.add_station, name='add_station'),
    path('sensor/add/', views.add_sensor, name='add_sensor'),
    path("refresh/", views.refresh_sensor_data, name="refresh"),
]
