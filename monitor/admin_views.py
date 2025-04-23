# admin_view.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Rig, WaterLevelData

def admin_required(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(admin_required)
def rig_list(request):
    rigs = Rig.objects.all()
    return render(request, 'monitor/rig_list.html', {'rigs': rigs})

@login_required
@user_passes_test(admin_required)
def rig_add(request):
    if request.method == 'POST':
        sensor_id = request.POST.get('sensor_id')
        location = request.POST.get('location')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        rig = Rig(sensor_id=sensor_id, location=location, latitude=latitude, longitude=longitude)
        rig.save()

        return redirect('rig_list')

    return render(request, 'monitor/rig_form.html')

@login_required
@user_passes_test(admin_required)
def water_level_list(request):
    water_levels = WaterLevelData.objects.all()
    return render(request, 'monitor/waterlevel_list.html', {'water_levels': water_levels})

@login_required
@user_passes_test(admin_required)
def water_level_add(request):
    if request.method == 'POST':
        rig_id = request.POST.get('rig_id')
        level = request.POST.get('level')
        temperature = request.POST.get('temperature')
        humidity = request.POST.get('humidity')

        rig = Rig.objects.get(id=rig_id)

        water_level = WaterLevelData(rig=rig, level=level, temperature=temperature, humidity=humidity)
        water_level.save()

        return redirect('water_level_list')

    rigs = Rig.objects.all()
    return render(request, 'monitor/waterlevel_form.html', {'rigs': rigs})