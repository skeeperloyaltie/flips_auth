from django.db import models
import pytz

class TimezoneSetting(models.Model):
    timezone = models.CharField(
        max_length=50,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC',
    )

    def __str__(self):
        return self.timezone
