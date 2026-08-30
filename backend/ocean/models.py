import uuid
from django.db import models
from django.conf import settings

# Check if GIS is active
HAS_GIS = 'django.contrib.gis' in settings.INSTALLED_APPS

class Region(models.Model):
    """Geographic boundaries (e.g., Natural Earth countries or specific marine zones)."""
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True, null=True)  # e.g., ISO, EEZ code
    
    if HAS_GIS:
        from django.contrib.gis.db import models as gis_models
        geom = gis_models.MultiPolygonField(srid=4326, blank=True, null=True)
    
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
    
    if HAS_GIS:
        from django.contrib.gis.db import models as gis_models
        geom = gis_models.PointField(srid=4326, blank=True, null=True)
    
    source = models.CharField(max_length=100, default='Copernicus')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.source} Obs at ({self.latitude}, {self.longitude}) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"