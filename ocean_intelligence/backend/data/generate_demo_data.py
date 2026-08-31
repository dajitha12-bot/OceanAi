import os
import csv
import json
import random
from datetime import datetime, timedelta

def generate_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(base_dir, 'scientific_papers'), exist_ok=True)
    
    # Define locations around Chennai Coast:
    # Zone A (Nearshore): Lat 13.0, Lng 80.3
    # Zone B (Shelf): Lat 13.1, Lng 80.6 (Highly suitable for Tuna)
    # Zone C (Deep Sea): Lat 13.2, Lng 81.0
    locations = [
        {"name": "Chennai Zone A (Nearshore)", "lat": 13.0, "lng": 80.3, "depth_range": (5, 20)},
        {"name": "Chennai Zone B (Shelf)", "lat": 13.1, "lng": 80.6, "depth_range": (30, 80)},
        {"name": "Chennai Zone C (Deep Sea)", "lat": 13.2, "lng": 81.0, "depth_range": (200, 1000)},
        {"name": "Arabian Sea North", "lat": 20.0, "lng": 65.0, "depth_range": (10, 500)},
        {"name": "Bay of Bengal South", "lat": 8.0, "lng": 85.0, "depth_range": (10, 1500)},
    ]
    
    # 1. Copernicus Ocean Observations
    obs_file = os.path.join(base_dir, 'copernicus_demo.csv')
    start_date = datetime.now() - timedelta(days=90)
    
    with open(obs_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'latitude', 'longitude', 'depth', 'temperature', 'salinity', 'chlorophyll', 'source'])
        
        for loc in locations:
            lat, lng = loc["lat"], loc["lng"]
            for d in range(90):
                date_val = start_date + timedelta(days=d)
                # Daily variation with seasonal trend
                base_t = 28.5 + 0.5 * random.uniform(-1, 1)
                base_s = 34.2 + 0.2 * random.uniform(-1, 1)
                base_c = 1.8 + 0.4 * random.uniform(-1, 1)
                
                # Zone-specific biases
                if "Zone B" in loc["name"]:
                    # Perfect tuna parameters: Temp ~ 29.1, Sal ~ 34.6, Chlorophyll ~ 2.1
                    base_t = 29.1 + 0.3 * random.uniform(-1, 1)
                    base_s = 34.6 + 0.1 * random.uniform(-1, 1)
                    base_c = 2.1 + 0.2 * random.uniform(-1, 1)
                elif "Zone A" in loc["name"]:
                    # Warm, lower salinity (runoff), high chlorophyll
                    base_t = 29.8 + 0.4 * random.uniform(-1, 1)
                    base_s = 32.8 + 0.5 * random.uniform(-1, 1)
                    base_c = 3.5 + 1.0 * random.uniform(-1, 1)
                elif "Zone C" in loc["name"]:
                    # Deep sea, cooler, clear water
                    base_t = 26.8 + 0.4 * random.uniform(-1, 1)
                    base_s = 35.1 + 0.2 * random.uniform(-1, 1)
                    base_c = 0.4 + 0.1 * random.uniform(-1, 1)
                
                # Add some environmental anomalies!
                # Inject a heatwave anomaly in Chennai Zone B around 15 days ago
                if "Zone B" in loc["name"] and 70 <= d <= 75:
                    base_t = 31.2 + 0.2 * random.uniform(-1, 1)  # Warm anomaly
                
                writer.writerow([
                    date_val.strftime('%Y-%m-%d %H:%M:%S'),
                    round(lat, 4),
                    round(lng, 4),
                    round(random.uniform(loc["depth_range"][0], loc["depth_range"][0] + 5), 1),
                    round(base_t, 2),
                    round(base_s, 2),
                    round(base_c, 2),
                    'Copernicus_Demo'
                ])
                
    # 2. OBIS Species Occurrences
    # Species: Yellowfin Tuna (Thunnus albacares), Indian Mackerel (Rastrelliger kanagurta), Common Dolphin (Delphinus delphis)
    species_list = [
        {
            "taxon_id": 127027,
            "scientific_name": "Thunnus albacares",
            "common_name": "Yellowfin Tuna",
            "rank": "Species",
            "taxonomy": {"kingdom": "Animalia", "phylum": "Chordata", "class": "Actinopterygii", "order": "Perciformes", "family": "Scombridae", "genus": "Thunnus"},
            "limits": {"temp_min": 25.0, "temp_max": 31.0, "sal_min": 33.5, "sal_max": 35.5, "chlor_min": 1.0, "chlor_max": 3.0}
        },
        {
            "taxon_id": 127021,
            "scientific_name": "Rastrelliger kanagurta",
            "common_name": "Indian Mackerel",
            "rank": "Species",
            "taxonomy": {"kingdom": "Animalia", "phylum": "Chordata", "class": "Actinopterygii", "order": "Perciformes", "family": "Scombridae", "genus": "Rastrelliger"},
            "limits": {"temp_min": 26.0, "temp_max": 32.0, "sal_min": 30.0, "sal_max": 34.5, "chlor_min": 2.0, "chlor_max": 6.0}
        },
        {
            "taxon_id": 137094,
            "scientific_name": "Delphinus delphis",
            "common_name": "Short-beaked Common Dolphin",
            "rank": "Species",
            "taxonomy": {"kingdom": "Animalia", "phylum": "Chordata", "class": "Mammalia", "order": "Artiodactyla", "family": "Delphinidae", "genus": "Delphinus"},
            "limits": {"temp_min": 10.0, "temp_max": 28.0, "sal_min": 32.0, "sal_max": 36.0, "chlor_min": 0.1, "chlor_max": 2.0}
        }
    ]
    
    species_file = os.path.join(base_dir, 'obis_species_demo.json')
    with open(species_file, 'w') as f:
        json.dump(species_list, f, indent=2)
        
    # Generate occurrences
    occurrence_file = os.path.join(base_dir, 'obis_occurrences_demo.csv')
    with open(occurrence_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['taxon_id', 'scientific_name', 'timestamp', 'latitude', 'longitude', 'depth', 'source'])
        
        # Yellowfin Tuna occurrences (mostly in Zone B and Zone C, preferring Zone B conditions)
        for d in range(45):
            date_val = start_date + timedelta(days=d*2)
            # Add Tuna in Zone B (shelf)
            writer.writerow([127027, "Thunnus albacares", date_val.strftime('%Y-%m-%d %H:%M:%S'), 13.1 + random.uniform(-0.05, 0.05), 80.6 + random.uniform(-0.05, 0.05), 45.0, 'OBIS_Demo'])
            # Add Tuna in Zone C (deep sea)
            writer.writerow([127027, "Thunnus albacares", date_val.strftime('%Y-%m-%d %H:%M:%S'), 13.2 + random.uniform(-0.08, 0.08), 81.0 + random.uniform(-0.08, 0.08), 100.0, 'OBIS_Demo'])
            
            # Add Indian Mackerel in Zone A (nearshore)
            writer.writerow([127021, "Rastrelliger kanagurta", date_val.strftime('%Y-%m-%d %H:%M:%S'), 13.0 + random.uniform(-0.04, 0.04), 80.3 + random.uniform(-0.04, 0.04), 10.0, 'OBIS_Demo'])
            
            # Add Dolphins in Zone C (deep sea)
            writer.writerow([137094, "Delphinus delphis", date_val.strftime('%Y-%m-%d %H:%M:%S'), 13.2 + random.uniform(-0.1, 0.1), 81.0 + random.uniform(-0.1, 0.1), 5.0, 'OBIS_Demo'])
            
    # 3. Natural Earth Boundaries (GeoJSON format, mocked for demo regions)
    # Generates regions representing Zone A, B, C and surrounding bay area
    regions_file = os.path.join(base_dir, 'natural_earth_demo.geojson')
    
    def get_poly_coords(center_lat, center_lng, size):
        return [
            [
                [center_lng - size, center_lat - size],
                [center_lng + size, center_lat - size],
                [center_lng + size, center_lat + size],
                [center_lng - size, center_lat + size],
                [center_lng - size, center_lat - size]  # Close polygon
            ]
        ]
        
    features = []
    for idx, loc in enumerate(locations):
        features.append({
            "type": "Feature",
            "id": idx + 1,
            "properties": {
                "name": loc["name"],
                "code": f"CH-{chr(65+idx)}" if idx < 3 else f"REG-{idx}",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": get_poly_coords(loc["lat"], loc["lng"], 0.15 if idx < 3 else 1.5)
            }
        })
        
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(regions_file, 'w') as f:
        json.dump(geojson_data, f, indent=2)

    # 4. RAG Scientific Texts
    report_text = """
    OCEANOGRAPHY AND SPECIES SUITABILITY REPORT: INDIAN OCEAN BIODIVERSITY & FISHERIES
    
    Abstract:
    This scientific text discusses the environmental thresholds and spatial distribution of major marine species in the Bay of Bengal, with a focus on Yellowfin Tuna (Thunnus albacares), Indian Mackerel (Rastrelliger kanagurta), and local cetaceans. 

    Yellowfin Tuna (Thunnus albacares) Environmental Suitability:
    Yellowfin tuna is a highly migratory pelagic species distributed in tropical and subtropical waters worldwide. In the Indian Ocean, especially near the continental shelf of the Coromandel Coast (Chennai regions), their distribution is highly influenced by sea surface temperature (SST), salinity, dissolved oxygen, and chlorophyll-a concentrations. 
    Studies show that the optimal temperature range for Yellowfin Tuna is between 25.0°C and 30.5°C. Salinity levels of 33.5 to 35.5 PSU are highly preferred, and chlorophyll concentrations of 1.0 to 2.8 mg/m³ signal high abundance of baitfish (such as anchovies and sardines), creating prime feeding zones. Thermal anomalies exceeding 31.0°C or dipping below 22°C significantly reduce suitability, triggering migratory shifts to deeper waters or higher latitudes.
    
    Indian Mackerel (Rastrelliger kanagurta) Coastal Abundance:
    The Indian Mackerel is a coastal pelagic species thriving in shallow, nutrient-rich estuarine and nearshore waters. Their suitability is strongly tied to river runoff, which lowers salinity (preferred 30.0 to 34.5 PSU) and triggers phytoplankton blooms. Mackerel feed on both phytoplankton and zooplankton, preferring high-chlorophyll environments (2.0 to 6.0 mg/m³). They are highly tolerant of warm tropical waters (26.0°C to 32.0°C), making nearshore coastal zones (Zone A) their primary habitat.

    Marine Anomaly & Biodiversity Risks in the Bay of Bengal:
    The Bay of Bengal is undergoing rapid climatic changes. Sea Surface Temperature anomalies (marine heatwaves) occur when the local temperature exceeds the 90th percentile of historical baselines. These thermal stress events reduce coral health, increase bleaching risks, and cause shifts in fish populations. When temperatures rise past 31°C, the risk to marine biodiversity scales from Moderate to High. This thermal stress combined with low salinity due to extreme monsoon precipitation can cause osmotic shock in marine invertebrates, decreasing local Shannon diversity indices.
    
    What-if Environmental Adaptations:
    A rise of 2.0°C in sea surface temperature under climate simulations shows a dramatic 20-30% decline in Yellowfin Tuna suitability in shallow shelf areas, forcing populations to migrate to deeper oceanic zones where temperatures remain within the thermocline (typically 20°C - 24°C). Under the same conditions, biodiversity risk rises to 68%, indicating a 'High Risk' state. This forces ecosystem restructuring.
    """
    
    with open(os.path.join(base_dir, 'scientific_papers', 'ocean_conservation_report.txt'), 'w', encoding='utf-8') as f:
        f.write(report_text)
        
    print("Demo dataset generated successfully in backend/data/ folder.")

if __name__ == "__main__":
    generate_data()
