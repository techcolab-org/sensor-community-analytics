from django import forms
from django.contrib.gis.geos import Point

from core.models import CoreSensorType
from .fetch_sensor_data_values import fetch_sensor_data_value
from .models import Station, Sensor, SensorType, ValueType
from .utils import get_sensor_details


class StationForm(forms.ModelForm):
    latitude = forms.FloatField(
        required=True,
        widget=forms.NumberInput(attrs={
            'step': 'any',
            'placeholder': '40.7128',
            'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all outline-none'
        })
    )
    longitude = forms.FloatField(
        required=True,
        widget=forms.NumberInput(attrs={
            'step': 'any',
            'placeholder': '-74.0060',
            'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all outline-none'
        })
    )

    class Meta:
        model = Station
        fields = ['name', 'sensor_uid','altitude', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Downtown Air Quality Monitor',
                'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all outline-none'
            }),
            'sensor_uid': forms.TextInput(attrs={
                'placeholder': 'e.g., esp8266-*******',
                'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all outline-none'
            }),
            'altitude': forms.NumberInput(attrs={
                'step': '0.1',
                'placeholder': 'Optional',
                'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all outline-none'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional description...',
                'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all outline-none resize-none'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-600 text-cyan-500 focus:ring-cyan-500/20 bg-dark-800'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['is_active'] = True
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')

        if lat is not None and lng is not None:
            cleaned_data['location'] = Point(lng, lat)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.location = self.cleaned_data.get('location')
        if self.cleaned_data.get('sensor_uid'):
            instance.sensor_uid = self.cleaned_data.get('sensor_uid')
        if commit:
            instance.save()
        return instance


class SensorForm(forms.ModelForm):
    sensor_type = forms.ModelChoiceField(
        queryset=CoreSensorType.objects.all(),
        empty_label="Select sensor type...",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all outline-none appearance-none cursor-pointer'
        })
    )

    class Meta:
        model = Sensor
        fields = ['sensor_id', 'sensor_type', 'description']
        widgets = {
            'sensor_id': forms.NumberInput(attrs={
                'placeholder': 'e.g., 12345 (optional)',
                'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all outline-none'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional sensor description...',
                'class': 'w-full px-4 py-3 rounded-xl bg-dark-800/50 border border-white/10 text-white placeholder-gray-500 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all outline-none resize-none'
            })
        }

    def __init__(self, *args, **kwargs):
        self.station = kwargs.pop('station', None)
        super().__init__(*args, **kwargs)
        self.fields['sensor_type'].queryset = CoreSensorType.objects.all()
        self.fields['sensor_type'].empty_label = "Select sensor type..."

    def clean(self):
        cleaned_data = super().clean()
        sensor_id = cleaned_data.get('sensor_id')
        form_sensor_type = cleaned_data.get('sensor_type')
        if not sensor_id:
            raise forms.ValidationError("Either sensor ID or sensor type must be provided.")
        sensor_details = get_sensor_details(sensor_id)
        if  sensor_details:
            station_changed = False

            if not self.station.altitude:
                self.station.altitude = sensor_details['station_altitude']
                station_changed = True

            if station_changed:
                self.station.save()


            manufacturer = sensor_details['sensor_type_manufacturer']
            name = sensor_details['sensor_type_name']

            sensor_type, created = SensorType.objects.get_or_create(
                manufacturer=manufacturer,
                name=name
            )

            if sensor_type.description is None:
                sensor_type.description = form_sensor_type.description if form_sensor_type and form_sensor_type.description else ''
                sensor_type.save()

            sensordatavalues = sensor_details['sensor_value_types']
            for item in sensordatavalues:
                value_type, created = ValueType.objects.get_or_create(name=item)
                value_type.value_type = item
                value_type.save()
        else:
            sensor_type, created = SensorType.objects.get_or_create(
                name=form_sensor_type.name,
            )

        cleaned_data['sensor_type'] = sensor_type
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.station:
            instance.station = self.station
        if commit:
            instance.sensor_type = self.cleaned_data['sensor_type']
            instance.save()
        fetch_sensor_data_value(instance)
        return instance