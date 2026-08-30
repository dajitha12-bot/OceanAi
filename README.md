# 🌊 AI Ocean Intelligence & Conversational Decision Platform

An AI-driven ocean intelligence system that automatically ingests spatial, taxonomic, and environmental datasets, trains machine learning models to identify species suitability and biodiversity risk, and integrates a conversational RAG/LLM assistant for real-time scientific decision support.

---

## 1. Project Objectives & AI Capabilities
The system is built as a scientific prototype designed to demonstrate:
- **Environmental Anomaly Detection**: Employs an unsupervised **Isolation Forest** (scikit-learn) to scan temperature, salinity, and chlorophyll-a values, alerting researchers of anomalies like marine heatwaves.
- **Species Suitability AI**: Employs a **Random Forest Classifier** trained on OBIS occurrences matched with Copernicus ocean observations. Falls back to a seasonal Gaussian biological suitability index when local data is sparse.
- **Ecosystem Risk Assessment**: Computes regional biodiversity indicators (Species Richness, Shannon Diversity Index) coupled with a model-derived risk score addressing thermal stress, osmotic shocks (salinity drop), and anomaly occurrences.
- **Conversational RAG Agent**: An LLM agent (Google Gemini or OpenAI) that dynamically parses query intent, triggers spatial/tabular DB queries, extracts relevant chunks from scientific papers (vector lookup), and synthesizes grounded answers.
- **What-If Simulation**: Allows analysts to adjust Temperature, Salinity, and Chlorophyll sliders, running immediate model inferences to compare "Before vs After" suitability and risk metrics.

---

## 2. Technology Stack
- **Backend**: Python, Django, Django REST Framework, PostgreSQL, PostGIS, pgvector
- **Frontend**: Vite, React, TypeScript, Tailwind CSS, Leaflet Map (react-leaflet), Recharts
- **AI/ML**: Scikit-learn, NumPy, Pandas
- **GenAI**: Google GenAI SDK, OpenAI SDK, PyPDF2 (text extraction)

---

## 3. Database Schema Architecture

The platform uses a single PostgreSQL database (`ocean_intelligence`) with PostGIS and pgvector.

```
+-------------------------------------------------------------------------------+
|                             ocean_intelligence                                |
+------------------------------------+------------------------------------------+
|  ocean_observations                |  fisheries (occurrences)                 |
|  - id: UUID (PK)                   |  - id: UUID (PK)                         |
|  - temperature: Float              |  - species: FK(species)                  |
|  - salinity: Float                 |  - timestamp: DateTime                   |
|  - chlorophyll: Float              |  - latitude: Float                       |
|  - depth: Float                    |  - longitude: Float                      |
|  - timestamp: DateTime             |  - geom: Point (PostGIS)                 |
|  - latitude, longitude: Float      |  - depth: Float                          |
|  - geom: Point (PostGIS)           |  - source: String                        |
|  - source: String                  +------------------------------------------+
+------------------------------------+  species                                 |
|  regions                           |  - id: Integer (Taxon ID)                |
|  - id: Integer (PK)                |  - scientific_name: String (Unique)      |
|  - name: String                    |  - common_name: String                   |
|  - code: String                    |  - taxon_rank: String                    |
|  - geom: MultiPolygon (PostGIS)    |  - taxonomy_data: JSON                   |
+------------------------------------+  - temp_min / temp_max: Float            |
|  biodiversity                      |  - salinity_min / salinity_max: Float    |
|  - id: UUID (PK)                   |  - chlorophyll_min / max: Float          |
|  - region: FK(regions)             +------------------------------------------+
|  - species_count: Integer          |  anomalies                               |
|  - occurrence_count: Integer       |  - id: UUID (PK)                         |
|  - shannon_index: Float            |  - parameter: String (temp/sal/chlor)    |
|  - risk_score: Float (0-100)       |  - observed_value: Float                 |
|  - risk_level: String              |  - expected_value: Float                 |
|  - geom: MultiPolygon (PostGIS)    |  - severity: String (Low/Medium/High)    |
+------------------------------------+  - geom: Point (PostGIS)                 |
|  ai_predictions                    |  - timestamp: DateTime                   |
|  - id: UUID (PK)                   |  - model_method: String                  |
|  - target_type: String             +------------------------------------------+
|  - target_id: String               |  document_chunks                         |
|  - prediction_date: Date           |  - id: UUID (PK)                         |
|  - predicted_value: Float          |  - document: FK(documents)               |
|  - geom: Point (PostGIS)           |  - chunk_index: Integer                  |
|  - features_used: JSON             |  - content: Text                         |
|  - model_version: String           |  - embedding: Vector(768) (pgvector)     |
+------------------------------------+------------------------------------------+
```

---

## 4. Manual Connection & Setup Steps

If running with a live PostgreSQL database, perform these steps:

### A. PostgreSQL Setup
1. Download and install PostgreSQL (v14 or higher recommended).
2. Create the target database using psql or pgAdmin:
   ```sql
   CREATE DATABASE ocean_intelligence;
   ```
3. Create a database user and grant privileges:
   ```sql
   CREATE USER ocean_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE ocean_intelligence TO ocean_user;
   ```
4. Set the `DATABASE_URL` in your `.env` file:
   ```env
   DATABASE_URL=postgis://ocean_user:secure_password@localhost:5432/ocean_intelligence
   ```

### B. PostGIS Extension
1. Install PostGIS matching your PostgreSQL version. On Windows, use the Application Stack Builder. On Ubuntu:
   ```bash
   sudo apt-get install postgresql-14-postgis-3
   ```
2. Connect to the database and enable the extension:
   ```sql
   \c ocean_intelligence;
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Set your GDAL path if on Windows (Settings auto-detects `C:\OSGeo4W` if installed there, otherwise set it in environment).

### C. pgvector Extension
1. Install pgvector on your database server.
   - On Windows: download binaries or compile using MSBuild.
   - On Linux/macOS:
     ```bash
     cd /tmp
     git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
     cd pgvector
     make
     make install # may require sudo
     ```
2. Connect to the database and enable the extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## 5. Ingestion Commands & Live Sources

To populate the database from the command line, use these Django commands:

### A. Copernicus Marine Ingestion
```bash
python manage.py ingest_copernicus --limit 100
```
- **Demo Mode**: By default, reads clean observations from `backend/data/copernicus_demo.csv`.
- **Live Mode**: If `COPERNICUS_USERNAME` and `COPERNICUS_PASSWORD` are set in `.env` and `DEMO_MODE=False`, queries Copernicus REST API.

### B. OBIS Ingestion
```bash
python manage.py ingest_obis --species "Thunnus albacares" --limit 50
```
- **Demo Mode**: Loads taxon metadata and occurrences from local demo files.
- **Live Mode**: Queries the public free OBIS API endpoint (`https://api.obis.org/v3`) for species taxon classifications and occurrence points.

### C. Natural Earth Boundaries
```bash
python manage.py import_natural_earth
```
- Reads boundary polygons from `backend/data/natural_earth_demo.geojson` representing Zone A, B, C, and Chennai regional waters, writing them to PostGIS geometry fields.

### D. RAG Scientific Documents
```bash
python manage.py ingest_documents
```
- Extracts text from PDFs and text files in `backend/data/scientific_papers/` (supporting `PyPDF2`), splits them into overlapping chunks, computes vectors, and inserts them into `pgvector` store.

---

## 6. Project Automation Breakdown

| Component | Antigravity Handles | User Manually Handles |
| :--- | :---: | :---: |
| Django project structure | ✅ | |
| Database schema & Django migrations | ✅ | |
| Copernicus & OBIS API integrations | ✅ | |
| ML models (anomaly, suitability, forecasts) | ✅ | |
| Dynamic vector chunks & RAG logic | ✅ | |
| Leaflet map overlays & Recharts components | ✅ | |
| PostgreSQL database installation | | ✅ |
| PostGIS & pgvector installation/activation | | ✅ |
| API keys (Gemini / OpenAI API keys) | | ✅ |

---

## 7. Quick Start (Run in Demo Mode)

To run the project locally on your machine:

### Backend Setup
1. Navigate to the `backend/` folder.
2. Initialize virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Ingest demo datasets:
   ```bash
   python manage.py ingest_copernicus --demo
   python manage.py ingest_obis --demo
   python manage.py import_natural_earth --demo
   python manage.py ingest_documents
   ```
7. Start development server:
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://127.0.0.1:8000/`.

### Frontend Setup
1. Navigate to the `frontend/` folder.
2. Install npm modules:
   ```bash
   npm install
   ```
3. Run Vite server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173/` in your browser.

---

## 8. AI Limitations & Future Scope
- **Biological Assumptions**: Suitability is calculated based on Sea Surface Temperature, Salinity, and Chlorophyll. In real-world oceanography, dissolved oxygen, currents, and thermocline depth are critical.
- **Pseudo-Absences**: ML model generates random pseudo-absences. Real ecological surveys use confirmed zero-catch surveys.
- **LLM Grounding**: If local document stores do not cover the specific query, fallback responses are used to maintain assistant stability.
