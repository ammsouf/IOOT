from rest_framework import serializers
from .models import Dht11 ,Incident
class DHT11serialize(serializers.ModelSerializer) :
    class Meta :
        model = Dht11
        fields ='__all__'
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['incident_id', 'status', 'start_time']