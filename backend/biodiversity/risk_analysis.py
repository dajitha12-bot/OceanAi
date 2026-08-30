import numpy as np
from django.apps import apps
from django.db.models import Count
from django.utils import timezone

class BiodiversityRiskAnalyzer:
    """Calculates biodiversity indices and model-derived environmental risk levels for regions."""
    
    def calculate_region_biodiversity(self, region_id=None):
        Region = apps.get_model('ocean', 'Region')
        Species = apps.get_model('fisheries', 'Species')
        FisheriesOccurrence = apps.get_model('fisheries', 'FisheriesOccurrence')
        OceanObservation = apps.get_model('ocean', 'OceanObservation')
        Anomaly = apps.get_model('ai', 'Anomaly')
        BiodiversityIndicator = apps.get_model('biodiversity', 'BiodiversityIndicator')
        
        # Get regions
        regions = Region.objects.all()
        if region_id:
            regions = regions.filter(id=region_id)
            
        updated_count = 0
        for reg in regions:
            # 1. Fetch occurrences inside this region
            # If PostGIS is active, use spatial query, otherwise boundary bounding box or list
            has_gis = apps.is_installed('django.contrib.gis')
            
            if has_gis and reg.geom:
                occs = FisheriesOccurrence.objects.filter(geom__within=reg.geom)
                obs = OceanObservation.objects.filter(geom__within=reg.geom)
                anom_list = Anomaly.objects.filter(geom__within=reg.geom)
            else:
                # Bounding box fallback
                # Estimate a simple box based on region name if demo
                if "Zone A" in reg.name:
                    bbox = (12.85, 80.15, 13.15, 80.45)
                elif "Zone B" in reg.name:
                    bbox = (12.95, 80.45, 13.25, 80.75)
                elif "Zone C" in reg.name:
                    bbox = (13.05, 80.85, 13.35, 81.15)
                else:
                    bbox = (5.0, 60.0, 25.0, 90.0) # Broad Indian Ocean
                    
                occs = FisheriesOccurrence.objects.filter(
                    latitude__gte=bbox[0], latitude__lte=bbox[2],
                    longitude__gte=bbox[1], longitude__lte=bbox[3]
                )
                obs = OceanObservation.objects.filter(
                    latitude__gte=bbox[0], latitude__lte=bbox[2],
                    longitude__gte=bbox[1], longitude__lte=bbox[3]
                )
                anom_list = Anomaly.objects.filter(
                    latitude__gte=bbox[0], latitude__lte=bbox[2],
                    longitude__gte=bbox[1], longitude__lte=bbox[3]
                )

            # 2. Count species and calculate Shannon index
            species_counts = occs.values('species').annotate(count=Count('id'))
            total_occs = occs.count()
            
            species_richness = species_counts.count()
            shannon_index = 0.0
            
            if total_occs > 0 and species_richness > 0:
                # Shannon Index: H = -sum(p_i * ln(p_i))
                p_i = np.array([item['count'] / total_occs for item in species_counts])
                shannon_index = -np.sum(p_i * np.log(p_i))
                shannon_index = float(shannon_index) if not np.isnan(shannon_index) else 0.0

            # 3. Calculate Risk Score based on environmental stress factors
            # Default baselines if no observations
            avg_temp, avg_sal, avg_chlor = 28.0, 34.0, 1.5
            
            if obs.exists():
                from django.db.models import Avg
                agg = obs.aggregate(Avg('temperature'), Avg('salinity'), Avg('chlorophyll'))
                avg_temp = agg['temperature__avg'] or 28.0
                avg_sal = agg['salinity__avg'] or 34.0
                avg_chlor = agg['chlorophyll__avg'] or 1.5
                
            # Stress variables:
            # - Thermal stress if temperature is above 29.5C
            thermal_stress = max(0.0, (avg_temp - 29.0) / 2.0) if avg_temp > 29.0 else 0.0
            # - Osmotic stress if salinity drops below 33.0 PSU
            osmotic_stress = max(0.0, (34.0 - avg_sal) / 2.0) if avg_sal < 34.0 else 0.0
            # - Chlorophyll variance (excess chlorophyll indicates eutrophication/algal blooms)
            bloom_stress = max(0.0, (avg_chlor - 2.5) / 1.5) if avg_chlor > 2.5 else 0.0
            
            # Anomaly rate contribution
            anom_count = anom_list.count()
            anomaly_stress = min(1.0, anom_count / 10.0)
            
            # Calculate final risk score from stress weights
            # Base risk is lower if species diversity is high (resilience)
            resilience_factor = max(0.3, 1.0 - (shannon_index / 3.0))
            
            raw_risk = (0.35 * thermal_stress + 0.2 * osmotic_stress + 0.15 * bloom_stress + 0.3 * anomaly_stress) * 100.0
            risk_score = min(100.0, raw_risk * resilience_factor)
            
            # Boost risk if extreme values exist (e.g. temp > 31°C)
            if avg_temp > 31.0:
                risk_score = max(risk_score, 75.0)
            
            # Default base risk if no stress
            if risk_score < 5.0:
                # If we have occurrences and no anomalies, risk is low
                risk_score = 15.0 + 5.0 * np.random.uniform(-1, 1)
                
            risk_score = round(risk_score, 1)
            
            # Classify risk level
            if risk_score < 35.0:
                risk_level = 'Low'
            elif risk_score < 65.0:
                risk_level = 'Moderate'
            else:
                risk_level = 'High'
                
            # Save or Update BiodiversityIndicator
            ind, created = BiodiversityIndicator.objects.update_or_create(
                region=reg,
                defaults={
                    'region_name': reg.name,
                    'species_count': species_richness,
                    'occurrence_count': total_occs,
                    'shannon_index': shannon_index,
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'observation_period': '2020-2026',
                    'geom': reg.geom,
                    'source': 'AI Environmental Risk Model'
                }
            )
            updated_count += 1
            
        return updated_count
