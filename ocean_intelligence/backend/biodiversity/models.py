import uuid
from django.contrib.gis.db import models
from ocean.models import Region

class BiodiversityIndicator(models.Model):
    """Calculated and AI-derived biodiversity indicators for regions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='biodiversity_indicators', blank=True, null=True)
    region_name = models.CharField(max_length=255, blank=True, null=True)  # Backup label
    
    species_count = models.IntegerField(default=0)
    occurrence_count = models.IntegerField(default=0)
    shannon_index = models.FloatField(blank=True, null=True, help_text="AI-derived/model-derived species diversity index")
    
    # Model derived risk indices
    risk_score = models.FloatField(default=0.0, help_text="AI-derived biodiversity risk score (0 to 100%)")
    risk_level = models.CharField(max_length=20, default='Low', help_text="Low, Moderate, High")
    
    observation_period = models.CharField(max_length=100, default='2020-2026')
    geom = models.MultiPolygonField(srid=4326, blank=True, null=True)
    
    source = models.CharField(max_length=100, default='AI Model')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.region.name if self.region else self.region_name
        return f"Biodiversity for {name} ({self.observation_period}) - Risk: {self.risk_score}% ({self.risk_level})"
