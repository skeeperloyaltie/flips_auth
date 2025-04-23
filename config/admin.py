from django.contrib import admin
from .models import TimezoneSetting

@admin.register(TimezoneSetting)
class TimezoneSettingAdmin(admin.ModelAdmin):
    list_display = ('timezone',)
