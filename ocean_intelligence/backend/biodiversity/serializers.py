from rest_framework import serializers
from biodiversity.models import BiodiversityIndicator

class BiodiversityIndicatorSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = BiodiversityIndicator
        fields = ['id', 'region', 'region_name', 'species_count', 'occurrence_count', 'shannon_index', 'risk_score', 'risk_level', 'observation_period', 'source', 'created_at']
