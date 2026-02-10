import requests
import time
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Sensor, SensorDataValue, ValueType

API_BASE = "https://data.sensor.community/airrohr/v1/sensor/"


def ts_now(inf_type=None):
    if inf_type == 'info':
        return f'[INFO] @ {int(time.time())} '

    elif inf_type == 'error':
        return f'[ERROR] @ {int(time.time())} '

    elif inf_type == 'warning':
        return f'[WARNING] @ {int(time.time())} '

    elif inf_type == 'success':
        return f'[SUCCESS] @ {int(time.time())} '

    return f'OCCURRED @ {int(time.time())} '


def fetch_and_store_sensor_data(
        sensors=None,
        stdout=None,
        stderr=None,
):
    """
    Fetch latest sensor data from Sensor.Community
    and store new SensorDataValue entries.

    :param sensors: Optional queryset or list of Sensor objects
    :param stdout: Optional stream for logging (e.g. BaseCommand.stdout)
    :param stderr: Optional stream for error logging
    """

    def log(msg):
        if stdout:
            stdout.write(msg)

    def error(msg):
        if stderr:
            stderr.write(msg)

    log(f"\n\n{timezone.now()}")
    log(f"{ts_now('info')} Fetching sensor data...")

    if sensors is None:
        sensors = Sensor.objects.select_related(
            "station",
            "sensor_type",
        ).all()

    for sensor in sensors:
        fetch_sensor_data_value(sensor, log, error)

    log("✅ Sensor data fetching completed.\n\n")


def fetch_sensor_data_value(sensor=None, log=None, error=None):
    api_url = f"{API_BASE}{sensor.sensor_id}/"
    if log:
        log(f"{ts_now('info')} → Fetching for sensor ID: {sensor.sensor_id} ({sensor})")

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data_points = response.json()

        for entry in data_points:
            raw_ts = entry.get("timestamp")
            timestamp = parse_datetime(raw_ts)

            if not timestamp:
                continue

            if timezone.is_naive(timestamp):
                try:
                    timestamp = timezone.make_aware(timestamp)
                except Exception as e:
                    if error:
                        error(
                            f"{ts_now('error')} ❌ Failed to make timestamp aware: "
                            f"{raw_ts} ({e})"
                        )
                    continue

            if SensorDataValue.objects.filter(
                    sensor=sensor,
                    timestamp=timestamp,
            ).exists():
                if log:
                    log(
                        f"{ts_now('info')} → Data for {sensor.sensor_id} "
                        f"at {timestamp} already exists. Skipping."
                    )
                    continue

            with transaction.atomic():
                for item in entry.get("sensordatavalues", []):
                    value_type = item.get("value_type")
                    value = item.get("value")

                    if not value_type or value is None:
                        continue

                    try:
                        measurement = ValueType.objects.get(
                            value_type=value_type
                        )
                    except ValueType.DoesNotExist:
                        if error:
                            error(
                                f"{ts_now('error')} ❌ ValueType "
                                f"{value_type} not found. Skipping."
                            )
                            continue

                    SensorDataValue.objects.create(
                        sensor=sensor,
                        measurement=measurement,
                        value=value,
                        timestamp=timestamp,
                    )
    except Exception as e:
        if error:
            error(f"{ts_now('error')} ⚠️ Error fetching data for {sensor.sensor_id}: {e}")
