from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WaterLevelData
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

@receiver(post_save, sender=WaterLevelData)
def broadcast_water_level_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    data = {
        'sensor_id': instance.rig.sensor_id,
        'level': instance.level,
        'temperature': instance.temperature,
        'humidity': instance.humidity,
        'timestamp': instance.timestamp.isoformat()
    }

    async_to_sync(channel_layer.group_send)(
        'realtime_data',
        {
            'type': 'send_data',
            'data': data
        }
    )
