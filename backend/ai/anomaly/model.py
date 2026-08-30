import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from django.apps import apps
from django.utils import timezone

from ai.feature_engineering.preprocess import clean_ocean_data

class OceanAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False
        self.baselines = {}  # Store baseline mean/std for variables

    def train(self):
        """Trains Isolation Forest on all available historical data."""
        OceanObservation = apps.get_model('ocean', 'OceanObservation')
        obs = OceanObservation.objects.all()
        
        if obs.count() < 10:
            raise ValueError("Insufficient data to train Isolation Forest.")
            
        df = pd.DataFrame([{
            'temperature': o.temperature,
            'salinity': o.salinity,
            'chlorophyll': o.chlorophyll
        } for o in obs])
        
        df = clean_ocean_data(df)
        
        # Calculate statistics
        for col in ['temperature', 'salinity', 'chlorophyll']:
            self.baselines[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()) if df[col].std() > 0 else 1.0
            }
            
        X = df[['temperature', 'salinity', 'chlorophyll']]
        self.model.fit(X)
        self.is_trained = True
        return len(df)

    def detect_anomalies(self, temperature, salinity, chlorophyll, latitude, longitude, timestamp=None):
        """
        Scans a set of inputs and returns list of anomalies if detected.
        Checks Temperature, Salinity, and Chlorophyll.
        """
        # Load baseline stats if empty
        if not self.baselines:
            self._load_fallback_baselines()

        results = []
        features = {'temperature': temperature, 'salinity': salinity, 'chlorophyll': chlorophyll}
        
        # 1. Isolation Forest check (Joint multivariate anomaly)
        is_anomaly_mv = False
        if self.is_trained:
            X_test = pd.DataFrame([[temperature, salinity, chlorophyll]], columns=['temperature', 'salinity', 'chlorophyll'])
            pred = self.model.predict(X_test)[0]
            if pred == -1:
                is_anomaly_mv = True
                
        # 2. Individual univariate check (z-score check)
        for param, val in features.items():
            mean = self.baselines[param]['mean']
            std = self.baselines[param]['std']
            
            z_score = abs(val - mean) / std if std > 0 else 0
            
            # Threshold: z-score > 2.0 (95% range) is moderate anomaly, > 3.0 is high severity
            if z_score > 2.0 or (is_anomaly_mv and z_score > 1.5):
                severity = 'High' if z_score > 3.0 else 'Medium'
                if z_score <= 2.0:
                    severity = 'Low'
                    
                results.append({
                    'parameter': param,
                    'observed_value': val,
                    'expected_value': round(mean, 2),
                    'severity': severity,
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timestamp or timezone.now(),
                    'model_method': 'Isolation Forest + Z-Score' if self.is_trained else 'Statistical Z-Score Baseline'
                })
                
        return results

    def _load_fallback_baselines(self):
        """Fallback baselines based on standard global marine values."""
        self.baselines = {
            'temperature': {'mean': 28.0, 'std': 1.2},
            'salinity': {'mean': 34.0, 'std': 0.8},
            'chlorophyll': {'mean': 1.5, 'std': 0.6}
        }
        
    def scan_and_save_new_observations(self):
        """Scans new observations and logs any detected anomalies into the database."""
        OceanObservation = apps.get_model('ocean', 'OceanObservation')
        Anomaly = apps.get_model('ai', 'Anomaly')
        
        # Try to train model
        try:
            self.train()
        except ValueError:
            self._load_fallback_baselines()
            
        # Get observations that haven't been scanned (not logged in anomaly database)
        # For simplicity, we scan observations added in the last 2 hours or just check all
        # and avoid duplicates
        obs_to_scan = OceanObservation.objects.all().order_by('-timestamp')[:100]
        
        anomaly_count = 0
        for obs in obs_to_scan:
            anom_results = self.detect_anomalies(
                obs.temperature, obs.salinity, obs.chlorophyll,
                obs.latitude, obs.longitude, obs.timestamp
            )
            
            for res in anom_results:
                # Avoid duplicates
                exists = Anomaly.objects.filter(
                    parameter=res['parameter'],
                    latitude=res['latitude'],
                    longitude=res['longitude'],
                    timestamp=res['timestamp']
                ).exists()
                
                if not exists:
                    anom = Anomaly(
                        parameter=res['parameter'],
                        observed_value=res['observed_value'],
                        expected_value=res['expected_value'],
                        severity=res['severity'],
                        latitude=res['latitude'],
                        longitude=res['longitude'],
                        timestamp=res['timestamp'],
                        model_method=res['model_method']
                    )
                    if apps.is_installed('django.contrib.gis'):
                        from django.contrib.gis.geos import Point
                        anom.geom = Point(obs.longitude, obs.latitude)
                        
                    anom.save()
                    anomaly_count += 1
                    
        return anomaly_count
