from django.contrib import admin
from . import models
from .models import Incident

# Register your models here.
admin.site.register(models.Dht11)

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_id', 'status', 'start_time', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('incident_id', 'status')

admin.site.register(Incident, IncidentAdmin)