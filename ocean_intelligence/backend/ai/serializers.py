from rest_framework import serializers
from ai.models import Anomaly, AIPrediction

class AnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = Anomaly
        fields = ['id', 'parameter', 'observed_value', 'expected_value', 'severity', 'latitude', 'longitude', 'timestamp', 'model_method', 'created_at']


class AIPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPrediction
        fields = ['id', 'target_type', 'target_id', 'latitude', 'longitude', 'prediction_date', 'predicted_value', 'features_used', 'model_version', 'created_at']
