import os

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404

from .fetch_sensor_data_values import fetch_and_store_sensor_data
from .forms import StationForm, SensorForm
from .models import Station


# Create your views here.
@login_required
def home(request):
    stations = Station.objects.all()
    # core_sensor_types = CoreSensorType.objects.all()

    # Stats
    total_locations = len(stations)
    active_sensors = sum(len(s.get_sensor_data) for s in stations if getattr(s, 'is_active', True))

    # Initialize empty forms - MAKE SURE THESE ARE PASSED
    station_form = StationForm()
    sensor_form = SensorForm()
    station_path = os.path.join(settings.BASE_DIR, 'sensor_data_by_station')

    context = {
        'stations': stations,
        'total_stations': total_locations,
        'active_sensors': active_sensors,
        'station_form': station_form,
        'sensor_form': sensor_form,
        'station_path': os.path.exists(station_path)
    }

    return render(request, 'home.html', context)


@require_POST
def add_station(request):
    form = StationForm(request.POST)
    if form.is_valid():
        station = form.save()
        messages.success(request, f'Station "{station.name}" created successfully!')
    else:
        for error in form.errors.values():
            messages.error(request, error)
    return redirect('sensor:home')


@require_POST
def add_sensor(request):
    station_id = request.POST.get('station')
    station = get_object_or_404(Station, id=station_id)

    form = SensorForm(request.POST, station=station)
    if form.is_valid():
        sensor = form.save()
        messages.success(request, f'Sensor added to "{station.name}" successfully!')
    else:
        for error in form.errors.values():
            messages.error(request, error)
    return redirect('sensor:home')


@login_required
def refresh_sensor_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    fetch_and_store_sensor_data()

    return JsonResponse({
        "status": "ok",
        "message": "Sensor data refreshed successfully"
    })
