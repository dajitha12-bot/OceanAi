from rest_framework import serializers
from ocean.models import Region, OceanObservation

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'code', 'geom']
        # Handle spatial geom as read-only geojson
        extra_kwargs = {
            'geom': {'read_only': True}
        }


class OceanObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OceanObservation
        fields = ['id', 'temperature', 'salinity', 'chlorophyll', 'depth', 'timestamp', 'latitude', 'longitude', 'source', 'created_at']
