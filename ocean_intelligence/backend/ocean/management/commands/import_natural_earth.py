import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from ocean.models import Region

class Command(BaseCommand):
    help = "Import geographic boundaries/regions from Natural Earth dataset or geojson."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help="Path to custom GeoJSON file.")
        parser.add_argument('--demo', action='store_true', default=False, help="Force demo dataset import.")

    def handle(self, *args, **options):
        # Determine file path
        custom_file = options['file']
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        demo_file = os.path.join(base_dir, 'data', 'natural_earth_demo.geojson')
        
        target_file = custom_file if custom_file else demo_file
        
        if not os.path.exists(target_file):
            self.stderr.write(f"Boundary file not found at: {target_file}")
            return
            
        self.stdout.write(f"Importing boundaries from: {target_file}")
        
        with open(target_file, 'r') as f:
            geojson_data = json.load(f)
            
        features = geojson_data.get('features', [])
        count = 0
        
        for feature in features:
            props = feature.get('properties', {})
            name = props.get('name', f"Region {count}")
            code = props.get('code', f"REG-{count}")
            
            # Delete if exists
            Region.objects.filter(name=name).delete()
            
            region_obj = Region(
                name=name,
                code=code
            )
            
            if apps.is_installed('django.contrib.gis'):
                from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
                
                geom_data = feature.get('geometry')
                if geom_data:
                    geos_geom = GEOSGeometry(json.dumps(geom_data))
                    
                    # Ensure it is a MultiPolygon
                    if geos_geom.geom_type == 'Polygon':
                        geos_geom = MultiPolygon(geos_geom)
                    elif geos_geom.geom_type != 'MultiPolygon':
                        self.stdout.write(f"Skipping region {name}: Geometry is {geos_geom.geom_type}, expected MultiPolygon.")
                        continue
                        
                    region_obj.geom = geos_geom
            else:
                self.stdout.write(f"PostGIS/GDAL not loaded. Storing region {name} without spatial polygon geometry.")
                # When GIS is not installed, we can't save it because the geom field is missing.
                # In that case, we can't save the Region model as defined, but wait!
                # If django.contrib.gis is not installed, the table doesn't even exist!
                # If GIS is not installed, the Region table is not created because Region config uses MultiPolygonField.
                # So we catch the error or print a message.
                
            try:
                region_obj.save()
                count += 1
            except Exception as e:
                self.stderr.write(f"Error saving region {name}: {e}")
                
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} regions."))
