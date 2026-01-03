from django.db import models
from django.utils import timezone


class Dht11(models.Model):
    temp = models.FloatField(null=True)
    hum = models.FloatField(null=True)
    dt = models.DateTimeField(auto_now_add=True, null=True)


class Measurement(models.Model):
    temperature = models.FloatField()
    humedite = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Temp: {self.temperature}°C, Hum: {self.humedite}%"


class Incident(models.Model):
    STATUS_CHOICES = [
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('en_attente', 'En attente'),
        ('critique', 'Critique'),
        ('ferme', 'Fermé'),
        ('non_resolu', 'Non résolu'),
    ]

    incident_id = models.AutoField(primary_key=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)  # NEW FIELD
    operator_1_comment = models.TextField(null=True, blank=True)
    operator_2_acknowledged = models.BooleanField(default=False)
    operator_3_acknowledged = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    counter = models.IntegerField(default=0)

    def __str__(self):
        return f"Incident {self.incident_id} - {self.status}"

    def duration(self):
        """Calculate incident duration"""
        if self.end_time:
            delta = self.end_time - self.start_time
            hours = delta.total_seconds() / 3600
            minutes = (delta.total_seconds() % 3600) / 60
            if hours >= 1:
                return f"{int(hours)}h {int(minutes)}min"
            else:
                return f"{int(minutes)}min"
        return "En cours"

    def duration_seconds(self):
        """Return duration in seconds for calculations"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class IncidentHistory(models.Model):
    """Track all changes to incidents for complete traceability"""
    ACTION_CHOICES = [
        ('created', 'Incident créé'),
        ('counter_increment', 'Compteur incrémenté'),
        ('resolved', 'Incident résolu'),
        ('comment_added', 'Commentaire ajouté'),
        ('comment_updated', 'Commentaire modifié'),
    ]

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='history')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()  # Detailed description of what happened
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    counter_value = models.IntegerField(null=True, blank=True)  # Counter at this point

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Historique d'incident"
        verbose_name_plural = "Historiques d'incidents"

    def __str__(self):
        return f"Incident #{self.incident.incident_id} - {self.get_action_display()} - {self.timestamp}"