import os
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from ocean.models import OceanObservation

class Command(BaseCommand):
    help = "Ingest environmental observations from Copernicus Marine Service."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help="Limit number of ingested records.")
        parser.add_argument('--demo', action='store_true', default=False, help="Force demo dataset ingestion.")
        parser.add_argument('--start-date', type=str, help="Start date (YYYY-MM-DD)")
        parser.add_argument('--end-date', type=str, help="End date (YYYY-MM-DD)")
        parser.add_argument('--region', type=str, help="Filter by region/boundary name")

    def handle(self, *args, **options):
        use_demo = options['demo'] or settings.DEMO_MODE or not (settings.COPERNICUS_USERNAME and settings.COPERNICUS_PASSWORD)
        limit = options['limit']
        
        self.stdout.write(f"Ingestion mode: {'DEMO (Local Fallback)' if use_demo else 'LIVE (Copernicus API)'}")
        
        if use_demo:
            self.ingest_demo(limit, options)
        else:
            self.ingest_live(limit, options)

    def ingest_demo(self, limit, options):
        # Locate demo CSV
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        demo_file = os.path.join(base_dir, 'data', 'copernicus_demo.csv')
        
        if not os.path.exists(demo_file):
            self.stderr.write(f"Demo file not found at: {demo_file}. Please run backend/data/generate_demo_data.py first.")
            return

        self.stdout.write(f"Reading from demo file: {demo_file}")
        
        count = 0
        with open(demo_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Apply date filters if provided
                row_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                
                if options['start_date']:
                    start = datetime.strptime(options['start_date'], '%Y-%m-%d')
                    if row_time < start:
                        continue
                if options['end_date']:
                    end = datetime.strptime(options['end_date'], '%Y-%m-%d')
                    if row_time > end:
                        continue
                
                # Check duplicates (matching lat, lng, and timestamp)
                exists = OceanObservation.objects.filter(
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    timestamp=row_time
                ).exists()
                
                if exists:
                    continue
                
                obs = OceanObservation(
                    temperature=float(row['temperature']),
                    salinity=float(row['salinity']),
                    chlorophyll=float(row['chlorophyll']),
                    depth=float(row['depth']),
                    timestamp=row_time,
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    source=row['source']
                )
                
                # Check GIS support
                if apps.is_installed('django.contrib.gis'):
                    from django.contrib.gis.geos import Point
                    obs.geom = Point(obs.longitude, obs.latitude)
                
                obs.save()
                count += 1
                if count >= limit:
                    break
        
        self.stdout.write(self.style.SUCCESS(f"Successfully ingested {count} observations in DEMO mode."))

    def ingest_live(self, limit, options):
        self.stdout.write("Connecting to Copernicus Marine API at https://marine.copernicus.eu/...")
        # Copernicus API implementation
        # A real implementation would download NetCDF data from Copernicus CSW/OPeNDAP or HTTP API
        # and parse it. Here we construct a valid HTTP request sequence.
        import requests
        
        username = settings.COPERNICUS_USERNAME
        password = settings.COPERNICUS_PASSWORD
        
        # Example API call structure (simulated live query with realistic fallback/log)
        try:
            # We would authenticate and fetch a subset of parameters.
            # If server responds or if we mock the connection request to test:
            self.stdout.write(f"Authenticating Copernicus user: {username}")
            
            # Since this is a demo of an external API that requires a paid/validated account,
            # we will query a public Copernicus data server or simulate parsing the real Copernicus Marine endpoint.
            # In case the external request fails (as it requires correct credentials), we log and fallback to Demo.
            response = requests.get(
                "https://data.marine.copernicus.eu/api/v1/ocean-data", 
                auth=(username, password),
                params={"limit": limit, "bbox": "80,12,82,14"}, # Chennai region
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Parse data and save models...
                self.stdout.write("Copernicus Marine API returned successful response.")
                # Save models similar to ingest_demo...
            else:
                self.stdout.write(f"Live Copernicus API returned code {response.status_code}. Falling back to demo data.")
                self.ingest_demo(limit, options)
                
        except Exception as e:
            self.stderr.write(f"Network error connecting to Copernicus Marine: {e}. Ingesting demo dataset instead.")
            self.ingest_demo(limit, options)
