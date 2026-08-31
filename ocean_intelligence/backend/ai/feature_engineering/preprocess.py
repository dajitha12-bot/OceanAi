import numpy as np
import pandas as pd
from datetime import datetime

def clean_ocean_data(df):
    """
    Cleans ocean observations dataframe.
    - Handles missing values using linear interpolation or mean imputation.
    - Removes duplicate coordinates/timestamps.
    - Standardizes column types and formats.
    - Validates latitude (-90 to 90) and longitude (-180 to 180).
    """
    if df.empty:
        return df
        
    # Copy to avoid side effects
    df = df.copy()
    
    # 1. Coordinate Validation
    df = df[(df['latitude'] >= -90) & (df['latitude'] <= 90)]
    df = df[(df['longitude'] >= -180) & (df['longitude'] <= 180)]
    
    # 2. Timestamp Normalization
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # 3. Handle Duplicates
    # Drop rows with same lat, lng, and timestamp (keep first)
    if 'timestamp' in df.columns:
        df = df.drop_duplicates(subset=['latitude', 'longitude', 'timestamp'], keep='first')
    else:
        df = df.drop_duplicates(subset=['latitude', 'longitude'], keep='first')
        
    # 4. Handle Missing Values
    # Sort by time first for time-series interpolation if possible
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp')
        
    numeric_cols = ['temperature', 'salinity', 'chlorophyll', 'depth']
    for col in numeric_cols:
        if col in df.columns:
            # First attempt: linear interpolation (good for time series)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].interpolate(method='linear', limit_direction='both')
            
            # Second attempt: Fill remaining NaNs with global mean if interpolation failed (e.g. single value)
            if df[col].isnull().any():
                col_mean = df[col].mean()
                # If column is completely empty, provide standard scientific baselines
                if pd.isna(col_mean):
                    baselines = {'temperature': 28.0, 'salinity': 34.0, 'chlorophyll': 1.0, 'depth': 0.0}
                    col_mean = baselines.get(col, 0.0)
                df[col] = df[col].fillna(col_mean)
                
    return df


def engineer_temporal_features(df):
    """
    Extracts month, season, and day of year to capture seasonal oceanographic cycles.
    """
    if df.empty or 'timestamp' not in df.columns:
        return df
        
    df = df.copy()
    df['month'] = df['timestamp'].dt.month
    df['day_of_year'] = df['timestamp'].dt.dayofyear
    
    # Season mapping (1: Winter, 2: Spring, 3: Summer, 4: Autumn)
    df['season'] = df['month'].apply(lambda m: (m%12 + 3)//3)
    
    return df
