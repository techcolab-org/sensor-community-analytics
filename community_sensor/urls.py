"""
URL patterns for sensor data download endpoints.
Add these to your urls.py file.
"""

from django.urls import path
from . import views

app_name = 'community_sensor'

# Add these to your existing urlpatterns
# urlpatterns = [
#     # Download data for selected stations
#     path('download/station-data/',
#          views.download_station_data,
#          name='download_station_data'),
#
#     # Download data for a specific sensor
#     path('download/sensor-data/',
#          views.download_specific_sensor,
#          name='download_specific_sensor'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('download/station/', views.download_station_data, name='download_station_data'),
    path('download/sensor/', views.download_specific_sensor, name='download_sensor_data'),
    # path('download/progress/', views.get_download_progress, name='download_progress'),

    path('', views.station_data_manager, name='station_data'),
    path('station-data/list/', views.StationDataListView.as_view(), name='station_data_list'),
    path('station-data/csv/', views.CsvViewerView.as_view(), name='station_data_csv'),
]
