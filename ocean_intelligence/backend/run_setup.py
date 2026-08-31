import os
import sys
import subprocess

def run_cmd(args):
    print(f"Running: {' '.join(args)}")
    try:
        res = subprocess.run(args, check=True, text=True)
        return res.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False

def main():
    print("=================================================================")
    # 1. Verify environment
    if not os.path.exists('manage.py'):
        print("❌ Error: Run this script from the backend directory.")
        sys.exit(1)
        
    print("🌊 AI Ocean Intelligence - Backend Auto-Setup Script 🌊")
    print("=================================================================")
    
    # 2. Database extension verification
    print("\n[Step 1/4] Running Database Extension Diagnostics...")
    try:
        from db_setup import verify_database_extensions
        verify_database_extensions()
    except ImportError:
        print("⚠️ Warning: db_setup.py diagnostic script missing. Skipping checks.")

    # 3. Generate Migrations
    print("\n[Step 2/4] Generating Django Migrations...")
    success = run_cmd([sys.executable, "manage.py", "makemigrations", "ocean", "fisheries", "biodiversity", "ai", "rag", "assistant"])
    if not success:
        print("❌ Migrations generation failed. Check that PostgreSQL/PostGIS and GDAL are installed.")
        sys.exit(1)

    # 4. Run Migrations
    print("\n[Step 3/4] Running migrations on PostgreSQL...")
    success = run_cmd([sys.executable, "manage.py", "migrate"])
    if not success:
        print("❌ Database migrations failed. Verify DATABASE_URL in .env.")
        sys.exit(1)

    # 5. Ingest Demo Datasets
    print("\n[Step 4/4] Ingesting fallback/demo datasets to seed database...")
    run_cmd([sys.executable, "manage.py", "ingest_copernicus", "--demo"])
    run_cmd([sys.executable, "manage.py", "ingest_obis", "--demo"])
    run_cmd([sys.executable, "manage.py", "import_natural_earth", "--demo"])
    run_cmd([sys.executable, "manage.py", "ingest_documents"])
    
    # Run risk calculations
    print("\n[Step 5/5] Re-calculating regional biodiversity risks & anomalies...")
    run_cmd([sys.executable, "manage.py", "shell", "-c", "from biodiversity.risk_analysis import BiodiversityRiskAnalyzer; BiodiversityRiskAnalyzer().calculate_region_biodiversity(); from ai.anomaly.model import OceanAnomalyDetector; OceanAnomalyDetector().scan_and_save_new_observations(); from ai.prediction.model import OceanConditionForecaster; OceanConditionForecaster().generate_and_save_forecasts()"])
    
    print("\n=================================================================")
    print("✅ setup complete. You can now start the server: python manage.py runserver")
    print("=================================================================")

if __name__ == "__main__":
    main()
