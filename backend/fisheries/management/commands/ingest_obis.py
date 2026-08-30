import os
import csv
import json
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from fisheries.models import Species, FisheriesOccurrence

class Command(BaseCommand):
    help = "Ingest marine species taxonomy and occurrence points from OBIS."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50, help="Limit number of occurrence points per species.")
        parser.add_argument('--demo', action='store_true', default=False, help="Force demo dataset ingestion.")
        parser.add_argument('--species', type=str, default="Thunnus albacares", help="Scientific name of species to search on OBIS API.")

    def handle(self, *args, **options):
        use_demo = options['demo'] or settings.DEMO_MODE
        limit = options['limit']
        search_species = options['species']
        
        self.stdout.write(f"OBIS Ingestion mode: {'DEMO (Local Fallback)' if use_demo else 'LIVE (OBIS API)'}")
        
        if use_demo:
            self.ingest_demo(limit)
        else:
            self.ingest_live(search_species, limit)

    def ingest_demo(self, limit):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        species_demo_file = os.path.join(base_dir, 'data', 'obis_species_demo.json')
        occurrences_demo_file = os.path.join(base_dir, 'data', 'obis_occurrences_demo.csv')
        
        if not os.path.exists(species_demo_file) or not os.path.exists(occurrences_demo_file):
            self.stderr.write("Demo files missing. Please generate demo data first.")
            return

        # 1. Ingest Species Taxa
        self.stdout.write("Ingesting Species from Demo dataset...")
        with open(species_demo_file, 'r') as f:
            species_data = json.load(f)
            for item in species_data:
                Species.objects.update_or_create(
                    scientific_name=item['scientific_name'],
                    defaults={
                        'id': item['taxon_id'],
                        'common_name': item['common_name'],
                        'taxon_rank': item['rank'],
                        'taxonomy_data': item['taxonomy'],
                        'temp_min': item['limits']['temp_min'],
                        'temp_max': item['limits']['temp_max'],
                        'salinity_min': item['limits']['sal_min'],
                        'salinity_max': item['limits']['sal_max'],
                        'chlorophyll_min': item['limits']['chlor_min'],
                        'chlorophyll_max': item['limits']['chlor_max'],
                        'source': 'OBIS_Demo'
                    }
                )

        # 2. Ingest Occurrences
        self.stdout.write("Ingesting Occurrences from Demo dataset...")
        count = 0
        with open(occurrences_demo_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                taxon_id = int(row['taxon_id'])
                try:
                    species_obj = Species.objects.get(id=taxon_id)
                except Species.DoesNotExist:
                    continue
                
                row_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                
                # Deduplicate
                exists = FisheriesOccurrence.objects.filter(
                    species=species_obj,
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    timestamp=row_time
                ).exists()
                
                if exists:
                    continue
                    
                occurrence = FisheriesOccurrence(
                    species=species_obj,
                    timestamp=row_time,
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    depth=float(row['depth']) if row['depth'] else None,
                    source=row['source']
                )
                
                if apps.is_installed('django.contrib.gis'):
                    from django.contrib.gis.geos import Point
                    occurrence.geom = Point(occurrence.longitude, occurrence.latitude)
                    
                occurrence.save()
                count += 1
                if count >= limit:
                    break

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {count} occurrences in DEMO mode."))

    def ingest_live(self, scientific_name, limit):
        self.stdout.write(f"Querying OBIS API for species: {scientific_name}...")
        
        # 1. Query Species Taxon information
        try:
            taxon_url = f"https://api.obis.org/v3/taxon?scientificname={scientific_name}"
            response = requests.get(taxon_url, timeout=10)
            if response.status_code != 200:
                self.stdout.write(f"Taxon API error {response.status_code}. Falling back to demo dataset.")
                self.ingest_demo(limit)
                return
                
            results = response.json().get('results', [])
            if not results:
                self.stderr.write(f"No species taxon found for name: {scientific_name} on OBIS. Falling back to demo.")
                self.ingest_demo(limit)
                return
                
            taxon_info = results[0]
            taxon_id = taxon_info.get('taxonID')
            
            # Map taxonomic details
            taxonomy_data = {
                'kingdom': taxon_info.get('kingdom', ''),
                'phylum': taxon_info.get('phylum', ''),
                'class': taxon_info.get('class', ''),
                'order': taxon_info.get('order', ''),
                'family': taxon_info.get('family', ''),
                'genus': taxon_info.get('genus', '')
            }
            
            species_obj, created = Species.objects.update_or_create(
                scientific_name=scientific_name,
                defaults={
                    'id': taxon_id,
                    'common_name': taxon_info.get('vernacularName', scientific_name.split()[1]),
                    'taxon_rank': taxon_info.get('taxonRank', 'species'),
                    'taxonomy_data': taxonomy_data,
                    # Fallback default limits (can be updated by suitability logic later)
                    'temp_min': 20.0,
                    'temp_max': 31.0,
                    'salinity_min': 33.0,
                    'salinity_max': 36.0,
                    'chlorophyll_min': 0.5,
                    'chlorophyll_max': 4.0,
                    'source': 'OBIS_API'
                }
            )
            self.stdout.write(f"Taxon: {species_obj.scientific_name} (ID: {taxon_id}) registered.")
            
            # 2. Query Occurrences
            occ_url = f"https://api.obis.org/v3/occurrence?scientificname={scientific_name}&limit={limit}"
            self.stdout.write(f"Fetching occurrences from OBIS: {occ_url}")
            response = requests.get(occ_url, timeout=15)
            if response.status_code != 200:
                self.stdout.write("Occurrences API error. Falling back to demo dataset.")
                self.ingest_demo(limit)
                return
                
            occ_results = response.json().get('results', [])
            count = 0
            
            for item in occ_results:
                lat = item.get('decimalLatitude')
                lng = item.get('decimalLongitude')
                date_str = item.get('eventDate')
                depth = item.get('depth')
                
                if lat is None or lng is None:
                    continue
                    
                # Parse date
                try:
                    # eventDate can be ISO string
                    if date_str:
                        # Clean date string (sometimes includes timezone info)
                        if 'Z' in date_str:
                            date_str = date_str.replace('Z', '')
                        if '+' in date_str:
                            date_str = date_str.split('+')[0]
                        row_time = datetime.fromisoformat(date_str)
                    else:
                        row_time = datetime.now()
                except Exception:
                    row_time = datetime.now()
                
                # Check duplicates
                exists = FisheriesOccurrence.objects.filter(
                    species=species_obj,
                    latitude=lat,
                    longitude=lng,
                    timestamp=row_time
                ).exists()
                
                if exists:
                    continue
                    
                occurrence = FisheriesOccurrence(
                    species=species_obj,
                    timestamp=row_time,
                    latitude=lat,
                    longitude=lng,
                    depth=depth,
                    source='OBIS_API'
                )
                
                if apps.is_installed('django.contrib.gis'):
                    from django.contrib.gis.geos import Point
                    occurrence.geom = Point(lng, lat)
                    
                occurrence.save()
                count += 1
                
            self.stdout.write(self.style.SUCCESS(f"Successfully ingested {count} occurrences from OBIS API."))

        except Exception as e:
            self.stderr.write(f"Error connecting to OBIS API: {e}. Falling back to demo dataset.")
            self.ingest_demo(limit)
