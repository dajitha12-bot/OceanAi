import json
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.apps import apps

from ocean.models import Region, OceanObservation
from ocean.serializers import RegionSerializer, OceanObservationSerializer
from ai.models import Anomaly
from ai.suitability.model import SpeciesSuitabilityModel

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all().order_by('name')
    serializer_class = RegionSerializer


class OceanObservationViewSet(viewsets.ModelViewSet):
    queryset = OceanObservation.objects.all().order_by('-timestamp')
    serializer_class = OceanObservationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        bbox = self.request.query_params.get('bbox')
        if bbox:
            try:
                coords = [float(c) for c in bbox.split(',')]
                if len(coords) == 4:
                    queryset = queryset.filter(
                        latitude__gte=coords[0],
                        longitude__gte=coords[1],
                        latitude__lte=coords[2],
                        longitude__lte=coords[3]
                    )
            except ValueError:
                pass
                
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
            
        return queryset


class MapLayersView(APIView):
    """Aggregates spatial datasets (regions, anomalies, observations) into GeoJSON format."""
    
    def get(self, request):
        has_gis = apps.is_installed('django.contrib.gis')
        
        # 1. Fetch Regions (enriched with risk & suitability calculations)
        regions = Region.objects.all()
        regions_features = []
        
        for reg in regions:
            # Fetch derived biodiversity indicators
            risk_score = 25.0
            risk_level = "Low"
            try:
                # Extract indicator if exists
                ind = reg.biodiversity_indicators.first()
                if ind:
                    risk_score = ind.risk_score
                    risk_level = ind.risk_level
            except Exception:
                pass
                
            # Fetch latest observations within 1 degree of center
            center_lat = 13.1
            center_lng = 80.6
            if has_gis and reg.geom:
                centroid = reg.geom.centroid
                center_lat = centroid.y
                center_lng = centroid.x
                
            obs = OceanObservation.objects.filter(
                latitude__gte=center_lat - 0.5, latitude__lte=center_lat + 0.5,
                longitude__gte=center_lng - 0.5, longitude__lte=center_lng + 0.5
            ).order_by('-timestamp').first()
            
            temp = obs.temperature if obs else 29.1
            sal = obs.salinity if obs else 34.6
            chlor = obs.chlorophyll if obs else 2.1
            
            # Calculate suitability for Yellowfin Tuna (Thunnus albacares)
            suit_model = SpeciesSuitabilityModel("Thunnus albacares")
            suit_res = suit_model.calculate_heuristic_suitability(temp, sal, chlor)
            
            # Handle geometry serialization
            geom_dict = None
            if has_gis and reg.geom:
                geom_dict = json.loads(reg.geom.geojson)
            else:
                # Custom mock bbox coords for Leaflet if PostGIS is not active
                if "Zone A" in reg.name:
                    bbox = [[[80.15, 12.85], [80.45, 12.85], [80.45, 13.15], [80.15, 13.15], [80.15, 12.85]]]
                elif "Zone B" in reg.name:
                    bbox = [[[80.45, 12.95], [80.75, 12.95], [80.75, 13.25], [80.45, 13.25], [80.45, 12.95]]]
                elif "Zone C" in reg.name:
                    bbox = [[[80.85, 13.05], [81.15, 13.05], [81.15, 13.35], [80.85, 13.35], [80.85, 13.05]]]
                else:
                    bbox = [[[80.0, 10.0], [83.0, 10.0], [83.0, 15.0], [80.0, 15.0], [80.0, 10.0]]]
                geom_dict = {"type": "Polygon", "coordinates": bbox}
                
            regions_features.append({
                "type": "Feature",
                "properties": {
                    "id": reg.id,
                    "name": reg.name,
                    "code": reg.code,
                    "biodiversity_risk": risk_score,
                    "risk_level": risk_level,
                    "tuna_suitability": suit_res,
                    "temperature": temp,
                    "salinity": sal,
                    "chlorophyll": chlor
                },
                "geometry": geom_dict
            })
            
        # 2. Fetch active anomalies
        anoms = Anomaly.objects.all().order_by('-timestamp')[:50]
        anoms_features = []
        
        for a in anoms:
            geom_dict = None
            if has_gis and a.geom:
                geom_dict = json.loads(a.geom.geojson)
            else:
                geom_dict = {"type": "Point", "coordinates": [a.longitude, a.latitude]}
                
            anoms_features.append({
                "type": "Feature",
                "properties": {
                    "id": str(a.id),
                    "parameter": a.parameter,
                    "observed_value": a.observed_value,
                    "expected_value": a.expected_value,
                    "severity": a.severity,
                    "timestamp": a.timestamp.strftime('%Y-%m-%d %H:%M') if a.timestamp else None,
                    "model_method": a.model_method
                },
                "geometry": geom_dict
            })
            
        return Response({
            "regions": {
                "type": "FeatureCollection",
                "features": regions_features
            },
            "anomalies": {
                "type": "FeatureCollection",
                "features": anoms_features
            }
        })
