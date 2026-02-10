from django.contrib import admin, messages
from django.contrib.gis.geos import Point
from django import forms
from leaflet.admin import LeafletGeoAdmin
from django.db.models.functions import Lower

from core.models import CoreSensorType
from .models import (Sensor, SensorDataValue, SensorType,
                     SensorTypeValueTypeMapping, Station, ValueType)
from .utils import get_sensor_details


class ReadOnlyUserStampedModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if change:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)


class StationAdminForm(forms.ModelForm):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)

    class Meta:
        model = Station
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # preload lat/long from map
        if self.instance and self.instance.location:
            self.fields["latitude"].initial = self.instance.location.y
            self.fields["longitude"].initial = self.instance.location.x

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get("latitude")
        lng = cleaned_data.get("longitude")

        # if lat/long is provided, override map value
        if lat is not None and lng is not None:
            cleaned_data["location"] = Point(lng, lat)

        return cleaned_data

@admin.register(Station)
class StationAdmin(LeafletGeoAdmin):
    form = StationAdminForm

    class Media:
        js = ("admin/js/leaflet_readonly.js",)

    list_display = (
        'id', 'name', 'sensor_uid', 'owner', 'description',
        'is_active', 'last_notify', 'kickoff_date'
    )
    list_display_links = list_display
    search_fields = ('name',)
    list_filter = ('is_active',)
    readonly_fields = ReadOnlyUserStampedModelAdmin.readonly_fields + ('uid',)


@admin.register(SensorType)
class SensorTypeAdmin(ReadOnlyUserStampedModelAdmin):
    list_display = ('id', 'name', 'manufacturer', 'description')
    list_display_links = list_display
    search_fields = ('name',)
    list_filter = ('manufacturer',)


@admin.register(ValueType)
class ValueTypeAdmin(ReadOnlyUserStampedModelAdmin):
    list_display = ('id', 'name', 'value_type',)
    list_display_links = list_display
    search_fields = ('name',)
    list_filter = ('value_type',)


@admin.register(Sensor)
class SensorAdmin(ReadOnlyUserStampedModelAdmin):
    list_display = (
        'id', 'sensor_id', 'station', 'sensor_type',
        'description', 'kickoff_date'
    )
    list_display_links = list_display
    list_filter = ('station', 'sensor_type',)

    def save_model(self, request, obj, form, change):
        core_sensor_type = None
        if not change and obj.sensor_id:
            try:
                sensor_details = get_sensor_details(obj.sensor_id)

                station_changed = False
                if not obj.station.altitude:
                    obj.station.altitude = sensor_details['station_altitude']
                    station_changed = True

                if not obj.station.location:
                    obj.station.location = f'POINT({sensor_details["station_longitude"]} {sensor_details["station_latitude"]})'
                    station_changed = True

                if station_changed:
                    obj.station.save()

                manufacturer = sensor_details['sensor_type_manufacturer']
                name = sensor_details['sensor_type_name']
                core_sensor_type_exists = CoreSensorType.objects.annotate(
                    name_lower=Lower('name'),
                ).filter(
                    name_lower = name.lower(),
                ).exists()

                if core_sensor_type_exists:
                    core_sensor_type = CoreSensorType.objects.annotate(
                        name_lower=Lower('name'),
                    ).get(
                        name_lower=name.lower(),
                    )

                sensor_type, created = SensorType.objects.get_or_create(
                    manufacturer=manufacturer,
                    name=name
                )
                if sensor_type.description is None:
                    sensor_type.description = core_sensor_type.description if core_sensor_type.description else ''
                    sensor_type.save()

                sensordatavalues = sensor_details['sensor_value_types']
                for item in sensordatavalues:
                    value_type, created = ValueType.objects.get_or_create(name=item)
                    value_type.value_type = item
                    value_type.save()

                obj.sensor_type = sensor_type

            except Exception as e:
                messages.set_level(request, messages.ERROR)
                messages.error(request, 'Could not save sensor')
                messages.error(request, f'Exception : {e}')
                return None

        return super().save_model(request, obj, form, change)


@admin.register(SensorDataValue)
class SensorDataValueAdmin(ReadOnlyUserStampedModelAdmin):
    list_display = (
        'id', 'sensor', 'value', 'measurement',
        'timestamp', 'created_at', 'updated_at'
    )
    list_display_links = list_display
    list_filter = ('sensor', 'measurement',)


@admin.register(SensorTypeValueTypeMapping)
class SensorTypeValueTypeMappingAdmin(ReadOnlyUserStampedModelAdmin):
    list_display = (
        'id', 'sensor_type', 'value_type', 'abbr',
        'created_at', 'updated_at'
    )
    list_display_links = list_display
    list_filter = ('sensor_type', 'value_type',)
