import uuid
from django.db import models
from django.conf import settings

# Check if GIS is active
HAS_GIS = 'django.contrib.gis' in settings.INSTALLED_APPS

class Anomaly(models.Model):
    """Environmental anomalies detected by AI models (e.g., Isolation Forest)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parameter = models.CharField(max_length=50, help_text="e.g., temperature, salinity, chlorophyll")
    observed_value = models.FloatField()
    expected_value = models.FloatField(help_text="Expected baseline/normal value")
    severity = models.CharField(max_length=20, default='Low', help_text="Low, Medium, High")
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    if HAS_GIS:
        from django.contrib.gis.db import models as gis_models
        geom = gis_models.PointField(srid=4326, blank=True, null=True)
    
    timestamp = models.DateTimeField()
    model_method = models.CharField(max_length=100, default='Isolation Forest')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.severity} Anomaly in {self.parameter}: {self.observed_value} vs {self.expected_value} (Expected)"


class AIPrediction(models.Model):
    """Future forecasts of environmental variables, suitability, or risk."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_type = models.CharField(max_length=50, help_text="e.g., temperature, salinity, chlorophyll, suitability, risk")
    target_id = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., species id, region id, or coordinates")
    
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    if HAS_GIS:
        from django.contrib.gis.db import models as gis_models
        geom = gis_models.PointField(srid=4326, blank=True, null=True)
    
    prediction_date = models.DateField()
    predicted_value = models.FloatField()
    
    features_used = models.JSONField(default=dict, blank=True, null=True)
    model_version = models.CharField(max_length=50, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['prediction_date']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f"Prediction for {self.target_type} ({self.target_id}) on {self.prediction_date}: {self.predicted_value}"