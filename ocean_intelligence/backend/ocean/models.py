import uuid
from django.contrib.gis.db import models

class Region(models.Model):
    """Geographic boundaries (e.g., Natural Earth countries or specific marine zones)."""
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True, null=True)  # e.g., ISO, EEZ code
    geom = models.MultiPolygonField(srid=4326)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OceanObservation(models.Model):
    """Copernicus Marine or other ocean/environmental observations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    temperature = models.FloatField(help_text="Sea Surface Temperature in Celsius")
    salinity = models.FloatField(help_text="Salinity in PSU")
    chlorophyll = models.FloatField(help_text="Chlorophyll concentration in mg/m3")
    depth = models.FloatField(default=0.0, help_text="Depth in meters")
    timestamp = models.DateTimeField()
    
    # Store explicit lat/lng coordinates alongside spatial geometry
    latitude = models.FloatField()
    longitude = models.FloatField()
    geom = models.PointField(srid=4326)
    
    source = models.CharField(max_length=100, default='Copernicus')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.source} Obs at ({self.latitude}, {self.longitude}) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
