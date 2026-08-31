import numpy as np
import pandas as pd
from datetime import datetime
from django.apps import apps

# Custom preprocessors
from ai.feature_engineering.preprocess import clean_ocean_data, engineer_temporal_features

class SpeciesSuitabilityModel:
    def __init__(self, species_scientific_name):
        self.species_name = species_scientific_name
        self.model = None
        self.is_trained = False
        
        # Load Species limits from database
        self.species_limits = self._get_species_limits()

    def _get_species_limits(self):
        """Loads species thresholds from DB or defaults to Yellowfin Tuna."""
        Species = apps.get_model('fisheries', 'Species')
        try:
            sp = Species.objects.get(scientific_name=self.species_name)
            return {
                'temp_min': sp.temp_min or 25.0,
                'temp_max': sp.temp_max or 31.0,
                'sal_min': sp.salinity_min or 33.5,
                'sal_max': sp.salinity_max or 35.5,
                'chlor_min': sp.chlorophyll_min or 1.0,
                'chlor_max': sp.chlorophyll_max or 3.0,
                'common_name': sp.common_name or self.species_name
            }
        except Exception:
            # Standard yellowfin tuna defaults
            return {
                'temp_min': 25.0, 'temp_max': 31.0,
                'sal_min': 33.5, 'sal_max': 35.5,
                'chlor_min': 1.0, 'chlor_max': 3.0,
                'common_name': 'Tuna'
            }

    def train(self):
        """
        Trains a Random Forest classifier mapping historical observations to species occurrences.
        If data is insufficient, raises ValueError so we fall back to heuristic index.
        """
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=30, max_depth=5, random_state=42)
        
        OceanObservation = apps.get_model('ocean', 'OceanObservation')
        FisheriesOccurrence = apps.get_model('fisheries', 'FisheriesOccurrence')
        Species = apps.get_model('fisheries', 'Species')
        
        try:
            sp = Species.objects.get(scientific_name=self.species_name)
        except Exception:
            raise ValueError(f"Species {self.species_name} not found in database.")
            
        occurrences = FisheriesOccurrence.objects.filter(species=sp)
        observations = OceanObservation.objects.all()
        
        if occurrences.count() < 5 or observations.count() < 10:
            raise ValueError("Insufficient data to train machine learning model.")
            
        # Convert to DataFrames
        occ_list = [{'latitude': o.latitude, 'longitude': o.longitude, 'timestamp': o.timestamp} for o in occurrences]
        obs_list = [{
            'latitude': o.latitude, 'longitude': o.longitude, 'timestamp': o.timestamp,
            'temperature': o.temperature, 'salinity': o.salinity, 'chlorophyll': o.chlorophyll
        } for o in observations]
        
        df_occ = pd.DataFrame(occ_list)
        df_obs = pd.DataFrame(obs_list)
        df_obs = clean_ocean_data(df_obs)
        
        # Match occurrences to nearest observations in space & time to create presence samples
        presences = []
        for _, occ in df_occ.iterrows():
            # Spatial distance approximation
            df_obs['dist'] = np.sqrt((df_obs['latitude'] - occ['latitude'])**2 + (df_obs['longitude'] - occ['longitude'])**2)
            # Find closest observation within 0.8 degrees
            closest = df_obs[df_obs['dist'] < 0.8]
            if not closest.empty:
                best_match = closest.sort_values(by='dist').iloc[0]
                presences.append({
                    'temperature': best_match['temperature'],
                    'salinity': best_match['salinity'],
                    'chlorophyll': best_match['chlorophyll'],
                    'latitude': occ['latitude'],
                    'longitude': occ['longitude'],
                    'month': occ['timestamp'].month if hasattr(occ['timestamp'], 'month') else datetime.now().month,
                    'target': 1
                })
                
        if len(presences) < 3:
            raise ValueError("Could not match occurrences to observation coordinates.")
            
        # Generate pseudo-absences
        absences = []
        for _, obs in df_obs.sample(min(len(df_obs), len(presences) * 2)).iterrows():
            dist_to_occs = np.sqrt((df_occ['latitude'] - obs['latitude'])**2 + (df_occ['longitude'] - obs['longitude'])**2)
            if dist_to_occs.min() > 0.5:
                absences.append({
                    'temperature': obs['temperature'],
                    'salinity': obs['salinity'],
                    'chlorophyll': obs['chlorophyll'],
                    'latitude': obs['latitude'],
                    'longitude': obs['longitude'],
                    'month': obs['timestamp'].month if hasattr(obs['timestamp'], 'month') else datetime.now().month,
                    'target': 0
                })
                
        if not absences:
            for _ in range(len(presences)):
                absences.append({
                    'temperature': self.species_limits['temp_min'] - 4.0,
                    'salinity': self.species_limits['sal_min'] - 4.0,
                    'chlorophyll': self.species_limits['chlor_min'] - 0.5,
                    'latitude': 13.0,
                    'longitude': 80.0,
                    'month': 6,
                    'target': 0
                })
                
        df_train = pd.DataFrame(presences + absences)
        X = df_train[['temperature', 'salinity', 'chlorophyll', 'latitude', 'longitude', 'month']]
        y = df_train['target']
        
        self.model.fit(X, y)
        self.is_trained = True
        return len(presences), len(absences)

    def calculate_suitability(self, temperature, salinity, chlorophyll, latitude, longitude, timestamp=None):
        """
        Predicts suitability percentage (0-100%).
        Uses Random Forest if trained, otherwise falls back to Gaussian heuristic index.
        """
        features_dict = {
            'temperature': temperature,
            'salinity': salinity,
            'chlorophyll': chlorophyll,
            'latitude': latitude,
            'longitude': longitude,
            'month': timestamp.month if timestamp else datetime.now().month
        }
        
        if self.is_trained and self.model:
            # Predict using Random Forest
            X_test = pd.DataFrame([features_dict])
            prob = self.model.predict_proba(X_test)[0][1] # Probability of Class 1
            suitability_score = round(prob * 100.0, 1)
            model_info = "Random Forest Classifier (ML)"
        else:
            # Fallback to Scientific Gaussian Heuristic
            suitability_score = self.calculate_heuristic_suitability(temperature, salinity, chlorophyll)
            model_info = "Gaussian Biological Thresholds (Heuristic Prototype)"
            
        # Feature contributions: calculate distances from optimal parameters
        contributions = {}
        for param, key_prefix, name in [('temperature', 'temp', 'Temperature'), ('salinity', 'sal', 'Salinity'), ('chlorophyll', 'chlor', 'Chlorophyll')]:
            min_val = self.species_limits.get(f"{key_prefix}_min", 0.0)
            max_val = self.species_limits.get(f"{key_prefix}_max", 100.0)
            val = features_dict[param]
            opt = (min_val + max_val) / 2.0
            
            tol = (max_val - min_val) / 2.0
            deviation = abs(val - opt)
            suit = max(0, 1.0 - (deviation / tol)) if tol > 0 else 0
            contributions[name] = round(suit * 100.0, 1)
            
        return {
            'species': self.species_limits['common_name'],
            'scientific_name': self.species_name,
            'suitability': suitability_score,
            'model': model_info,
            'contributing_features': contributions,
            'is_ml': self.is_trained
        }

    def calculate_heuristic_suitability(self, temp, sal, chlor):
        """Gaussian suitability formula."""
        def gaussian_suitability(val, min_val, max_val):
            if val is None or min_val is None or max_val is None:
                return 1.0
            opt = (min_val + max_val) / 2.0
            sigma = (max_val - min_val) / 4.0
            if sigma == 0:
                return 1.0
            return np.exp(-((val - opt) ** 2) / (2 * (sigma ** 2)))

        s_temp = gaussian_suitability(temp, self.species_limits['temp_min'], self.species_limits['temp_max'])
        s_sal = gaussian_suitability(sal, self.species_limits['sal_min'], self.species_limits['sal_max'])
        s_chlor = gaussian_suitability(chlor, self.species_limits['chlor_min'], self.species_limits['chlor_max'])
        
        suitability = s_temp * s_sal * s_chlor
        return round(suitability * 100.0, 1)
