# datasync/admin.py
from django.contrib import admin
from .models import SyncActivity

@admin.register(SyncActivity)
class SyncActivityAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'table_name', 'records_updated')
    list_filter = ('table_name', 'timestamp')