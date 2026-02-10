import uuid
from datetime import datetime, time, timezone
from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.cache import cache

from core.models import TimeStampedModel, UserStampedModel
from .utils import reverse_geocode

User = get_user_model()

# Create your models here.
class Station(TimeStampedModel, UserStampedModel):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    sensor_uid = models.CharField(max_length=100, unique=True, blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT,
        null=True, blank=True
    )
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    location = models.PointField(null=True, blank=True, default=None,)
    altitude = models.FloatField(null=True, blank=True)
    last_notify = models.DateTimeField(null=True, blank=True)
    kickoff_date = models.DateTimeField(auto_now_add=True)
    location_display_name = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sensor_uid:
            self.sensor_uid = str(self.uid)
        if self.location and not self.location_display_name:
            geocoded = reverse_geocode(self.location)
            self.location_display_name = geocoded.get('display_name', '')
        super().save(*args, **kwargs)

    @property
    def location_name(self):
        if not self.location_display_name:
            geocoded = reverse_geocode(self.location)
            self.location_display_name = geocoded.get('display_name', '')
            self.save()

        return self.location_display_name

    @property
    def get_sensor_data(self):
        sensor_data = Sensor.objects.filter(station=self)
        return sensor_data


class SensorType(TimeStampedModel, UserStampedModel):
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255, default='')
    description = models.CharField(
        max_length=10000,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('name', 'manufacturer')

    def __str__(self):
        return self.name


class ValueType(TimeStampedModel, UserStampedModel):
    name = models.CharField(max_length=255)
    value_type = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Sensor(TimeStampedModel, UserStampedModel):
    sensor_id = models.BigIntegerField(
        unique=True,
        null=True, blank=True
    )
    station = models.ForeignKey(
        Station, related_name='sensors',
        on_delete=models.PROTECT
    )
    sensor_type = models.ForeignKey(
        SensorType, on_delete=models.PROTECT,
        blank=True
    )
    description = models.TextField(null=True, blank=True)
    kickoff_date = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('station', 'sensor_type')

    def clean(self):
        if not self.sensor_id and not self.sensor_type_id:
            raise ValidationError('Either sensor_id or sensor_type must be set.')
        return super().clean()

    def __str__(self) -> str:
        return f'{self.station.name}-{self.sensor_type.name}'

    @property
    def get_sensor_data_value(self):
        # ---- 1. TODAY (local, matches admin) ----
        today = datetime.now().date()
        start_dt = datetime.combine(today, time.min)
        end_dt = datetime.combine(today, time.max)

        # ---- 2. Which measurements we want ----
        sensor_name = self.sensor_type.name.upper()

        if "SDS011" in sensor_name:
            wanted = ["P1", "P2"]

        elif "BMP180" in sensor_name:
            wanted = ["pressure", "temperature", "pressure_at_sealevel"]

        elif "DHT22" in sensor_name:
            wanted = ["temperature", "humidity"]

        else:
            wanted = None  # fallback

        # ---- 3. Base queryset (today only) ----
        qs = (
            self.sensordatavalues
            .filter(timestamp__range=(start_dt, end_dt))
            .select_related("measurement")
            .order_by("-timestamp")
        )

        # ---- 4. Fallback: return first value ----
        if not wanted:
            first = qs.first()
            return {first.measurement.name: first} if first else {}

        # ---- 5. Latest value PER measurement ----
        result = {}
        for value in qs:
            name = value.measurement.name
            if name in wanted and name not in result:
                result[name] = value

        return result


class SensorDataValue(TimeStampedModel, UserStampedModel):
    timestamp = models.DateTimeField()
    sensor = models.ForeignKey(
        Sensor, related_name='sensordatavalues',
        on_delete=models.PROTECT
    )
    value = models.TextField(null=False)
    measurement = models.ForeignKey(ValueType, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return f'{self.measurement.name}-{self.value}'


class SensorTypeValueTypeMapping(TimeStampedModel, UserStampedModel):
    sensor_type = models.ForeignKey(
        SensorType, on_delete=models.PROTECT
    )
    value_type = models.ForeignKey(
        ValueType, on_delete=models.PROTECT
    )
    abbr = models.CharField(
        max_length=5, unique=False,
        blank=True, null=True
    )

    class Meta:
        unique_together = ('sensor_type', 'value_type')

    def __str__(self) -> str:
        return f'{self.sensor_type}-{self.value_type}'

    def save(self, *args, **kwargs):
        if not self.abbr:
            st = (self.sensor_type.name or "").strip().lower()
            vt = (self.value_type.name or "").strip().lower()

            if not st or not vt:
                raise ValidationError("sensor_type.name and value_type.name are required to generate abbr.")

            s1 = st[0]
            v2 = vt[:2]
            v3 = vt[:3]

            cand1 = f"{s1}{v2}"
            cand2 = f"{s1}{v3}"

            qs = SensorTypeValueTypeMapping.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if not qs.filter(abbr=cand1).exists():
                self.abbr = cand1
            elif not qs.filter(abbr=cand2).exists():
                self.abbr = cand2
            else:
                raise ValidationError(
                    f"Abbr collision for '{cand1}' and '{cand2}'. Please enter abbr manually."
                )

        super().save(*args, **kwargs)