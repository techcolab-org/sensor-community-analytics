from django.contrib import admin

from .models import CoreSensorType


@admin.register(CoreSensorType)
class CoreSensorTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'description')
    list_display_links = list_display
