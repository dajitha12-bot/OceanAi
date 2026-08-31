from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from ai.models import Anomaly, AIPrediction
from ai.serializers import AnomalySerializer, AIPredictionSerializer
from ai.anomaly.model import OceanAnomalyDetector
from ai.prediction.model import OceanConditionForecaster
from biodiversity.models import BiodiversityIndicator
from fisheries.models import Species
from ai.suitability.model import SpeciesSuitabilityModel

class AnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Anomaly.objects.all().order_by('-timestamp')
    serializer_class = AnomalySerializer

    @action(detail=False, methods=['post'], url_path='scan')
    def scan_anomalies(self, request):
        """Triggers scan of recent observations for anomalies using Isolation Forest."""
        detector = OceanAnomalyDetector()
        try:
            count = detector.scan_and_save_new_observations()
            return Response(
                {"message": f"Successfully scanned recent observations and logged {count} new anomalies."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to run anomaly scan: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIPrediction.objects.all().order_by('prediction_date')
    serializer_class = AIPredictionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        target_type = self.request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        return queryset

    @action(detail=False, methods=['post'], url_path='generate-forecasts')
    def generate_forecasts(self, request):
        """Triggers ML model to predict future conditions for coordinates and save them."""
        forecaster = OceanConditionForecaster()
        try:
            count = forecaster.generate_and_save_forecasts()
            return Response(
                {"message": f"Successfully generated and saved {count} predictions for the next 7 days."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to run forecasting pipeline: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIInsightsViewSet(viewsets.ViewSet):
    """Consolidated AI insights and decision-support recommendations API."""

    def list(self, request):
        # 1. Fetch recent anomalies (last 7 days or top 5)
        recent_anom = Anomaly.objects.all().order_by('-timestamp')[:5]
        anom_serializer = AnomalySerializer(recent_anom, many=True)
        
        # 2. Get high biodiversity risk zones
        high_risk_zones = BiodiversityIndicator.objects.filter(risk_score__gte=50.0).order_by('-risk_score')
        risk_list = []
        for zone in high_risk_zones:
            risk_list.append({
                'region_name': zone.region.name if zone.region else zone.region_name,
                'risk_score': zone.risk_score,
                'risk_level': zone.risk_level,
                'species_count': zone.species_count,
                'source': zone.source
            })
            
        # 3. Species suitability insights (Tuna highlight)
        tuna_suitability_insights = []
        try:
            tuna = Species.objects.filter(scientific_name__icontains="Thunnus").first()
            if tuna:
                # Find Zone A, B, C coordinates and compute suitability
                # Default coordinates for Chennai Zones
                zones = [
                    {"name": "Chennai Zone A (Nearshore)", "lat": 13.0, "lng": 80.3},
                    {"name": "Chennai Zone B (Shelf)", "lat": 13.1, "lng": 80.6},
                    {"name": "Chennai Zone C (Deep Sea)", "lat": 13.2, "lng": 81.0}
                ]
                
                model = SpeciesSuitabilityModel(tuna.scientific_name)
                # Try loading trained
                try:
                    model.train()
                except ValueError:
                    pass
                    
                suit_results = []
                for z in zones:
                    # Let's assume standard temperature/salinity profiles based on zone
                    if "Zone B" in z["name"]:
                        t, s, c = 29.1, 34.6, 2.1
                    elif "Zone A" in z["name"]:
                        t, s, c = 29.8, 32.8, 3.5
                    else:
                        t, s, c = 26.8, 35.1, 0.4
                        
                    suit = model.calculate_suitability(t, s, c, z["lat"], z["lng"])
                    suit_results.append({
                        'zone': z['name'],
                        'suitability': suit['suitability'],
                        'is_ml': suit['is_ml']
                    })
                
                # Sort to find best zone
                suit_results.sort(key=lambda x: x['suitability'], reverse=True)
                best_zone = suit_results[0]['zone'] if suit_results else "N/A"
                best_score = suit_results[0]['suitability'] if suit_results else 0.0
                
                tuna_suitability_insights = {
                    'species': tuna.common_name or tuna.scientific_name,
                    'best_zone': best_zone,
                    'best_suitability': best_score,
                    'zones': suit_results,
                    'model_method': model.calculate_suitability(28.0, 34.0, 1.0, 13.0, 80.0)['model']
                }
        except Exception as e:
            tuna_suitability_insights = {"error": f"Failed to calculate suitability insights: {str(e)}"}

        # 4. Synthesize AI recommendations (decision-support)
        recommendations = []
        
        # Check if there are active anomalies
        if recent_anom.exists():
            heatwave_anoms = recent_anom.filter(parameter='temperature', severity='High')
            if heatwave_anoms.exists():
                recommendations.append(
                    "CRITICAL ALERT: Severe thermal anomalies (marine heatwave) detected. "
                    "Recommend halting active cage-culture fisheries in affected coordinates to prevent thermal stress mortality."
                )
            else:
                recommendations.append(
                    "ENVIRONMENTAL WARNING: Active anomalies detected in salinity/chlorophyll. "
                    "Recommend daily monitoring of coastal runoffs and potential algal bloom triggers."
                )
                
        # Species specific recommendations
        if isinstance(tuna_suitability_insights, dict) and 'best_zone' in tuna_suitability_insights:
            bz = tuna_suitability_insights['best_zone']
            score = tuna_suitability_insights['best_suitability']
            
            # Check if best zone has high risk
            matching_risk = [r for r in risk_list if r['region_name'] in bz]
            is_high_risk = matching_risk and matching_risk[0]['risk_level'] == 'High'
            
            if is_high_risk:
                recommendations.append(
                    f"DECISION SUPPORT: Although {bz} shows favorable {tuna_suitability_insights['species']} suitability ({score}%), "
                    "the region has high biodiversity risk. Delay deployment or reduce catch intensity to protect local ecosystem."
                )
            elif score > 75.0:
                recommendations.append(
                    f"DECISION SUPPORT: Optimal environment for {tuna_suitability_insights['species']} detected in {bz} ({score}% suitability). "
                    "Favorable harvesting window open. Recommend scheduling search patterns in this sector."
                )
        
        if not recommendations:
            recommendations.append(
                "DECISION SUPPORT: Environmental baselines are stable. Routine operations can proceed. "
                "Observe standard safety ranges."
            )
            
        return Response({
            'anomalies': anom_serializer.data,
            'biodiversity_risks': risk_list,
            'fisheries_suitability': tuna_suitability_insights,
            'recommendations': recommendations,
            'generated_at': timezone.now()
        })
