from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from fisheries.models import Species, FisheriesOccurrence
from fisheries.serializers import SpeciesSerializer, FisheriesOccurrenceSerializer
from ocean.models import OceanObservation
from ai.suitability.model import SpeciesSuitabilityModel

class SpeciesViewSet(viewsets.ModelViewSet):
    queryset = Species.objects.all().order_by('scientific_name')
    serializer_class = SpeciesSerializer


class FisheriesOccurrenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FisheriesOccurrence.objects.all().order_by('-timestamp')
    serializer_class = FisheriesOccurrenceSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        species_id = self.request.query_params.get('species')
        if species_id:
            queryset = queryset.filter(species_id=species_id)
        return queryset


class FisheriesIntelligenceViewSet(viewsets.ViewSet):
    """Custom API endpoints for fisheries suitability analysis."""
    
    @action(detail=False, methods=['get'], url_path='suitability')
    def get_suitability(self, request):
        species_name = request.query_params.get('species', 'Thunnus albacares')
        lat_param = request.query_params.get('latitude')
        lng_param = request.query_params.get('longitude')
        
        if not lat_param or not lng_param:
            return Response(
                {"error": "Please provide latitude and longitude parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            lat = float(lat_param)
            lng = float(lng_param)
        except ValueError:
            return Response({"error": "Invalid coordinate formats."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Fetch latest observation near these coordinates (within 0.5 degrees)
        # Sort by proximity first, then timestamp descending
        obs_query = OceanObservation.objects.all()
        # Simple distance ordering:
        obs = None
        if obs_query.exists():
            # Add field dist
            matches = []
            for o in obs_query.order_by('-timestamp')[:50]:
                dist = ((o.latitude - lat)**2 + (o.longitude - lng)**2)**0.5
                if dist <= 1.0:
                    matches.append((dist, o))
            if matches:
                # Get closest
                matches.sort(key=lambda x: x[0])
                obs = matches[0][1]
                
        # Fallback values if no observation found close by
        if obs:
            temp = obs.temperature
            sal = obs.salinity
            chlor = obs.chlorophyll
            obs_time = obs.timestamp
            source_obs = "Copernicus Observations Near Location"
        else:
            # Chennai regional defaults
            temp, sal, chlor = 29.1, 34.6, 2.1
            obs_time = None
            source_obs = "Global Climatology Default (No local observation found)"
            
        # 2. Run Suitability Inference
        model = SpeciesSuitabilityModel(species_name)
        
        # Try to train the model first if data is available
        try:
            model.train()
        except ValueError as e:
            # Fine if it fails, will use biological heuristic threshold model
            pass
            
        result = model.calculate_suitability(
            temperature=temp,
            salinity=sal,
            chlorophyll=chlor,
            latitude=lat,
            longitude=lng,
            timestamp=obs_time
        )
        
        # Add situational metadata
        result['current_conditions'] = {
            'temperature': temp,
            'salinity': sal,
            'chlorophyll': chlor,
            'timestamp': obs_time,
            'source': source_obs
        }
        
        return Response(result)
