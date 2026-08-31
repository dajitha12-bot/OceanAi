from rest_framework import serializers
from fisheries.models import Species, FisheriesOccurrence

class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = '__all__'


class FisheriesOccurrenceSerializer(serializers.ModelSerializer):
    species_name = serializers.ReadOnlyField(source='species.scientific_name')
    common_name = serializers.ReadOnlyField(source='species.common_name')

    class Meta:
        model = FisheriesOccurrence
        fields = ['id', 'species', 'species_name', 'common_name', 'timestamp', 'latitude', 'longitude', 'depth', 'source']
