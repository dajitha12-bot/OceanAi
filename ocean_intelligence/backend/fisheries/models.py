import uuid
from django.db import models
from django.conf import settings

# Check if GIS is active
HAS_GIS = 'django.contrib.gis' in settings.INSTALLED_APPS

class Species(models.Model):
    """Marine species/fisheries taxonomic information and environmental thresholds."""
    scientific_name = models.CharField(max_length=255, unique=True)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    taxon_rank = models.CharField(max_length=50, blank=True, null=True)
    taxonomy_data = models.JSONField(default=dict, help_text="Hierarchy: Kingdom, Phylum, Class, Order, Family, Genus")
    
    # Environmental ranges (scientific thresholds for suitability indexing)
    temp_min = models.FloatField(blank=True, null=True)
    temp_max = models.FloatField(blank=True, null=True)
    salinity_min = models.FloatField(blank=True, null=True)
    salinity_max = models.FloatField(blank=True, null=True)
    chlorophyll_min = models.FloatField(blank=True, null=True)
    chlorophyll_max = models.FloatField(blank=True, null=True)
    
    source = models.CharField(max_length=100, default='OBIS')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.common_name or self.scientific_name


class FisheriesOccurrence(models.Model):
    """Species occurrences data from OBIS for distribution modeling."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='occurrences')
    timestamp = models.DateTimeField()
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    if HAS_GIS:
        from django.contrib.gis.db import models as gis_models
        geom = gis_models.PointField(srid=4326, blank=True, null=True)
    
    depth = models.FloatField(blank=True, null=True)
    source = models.CharField(max_length=100, default='OBIS')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.species.scientific_name} occurrence at ({self.latitude}, {self.longitude})"