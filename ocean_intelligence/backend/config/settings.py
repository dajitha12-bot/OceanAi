import os
import platform
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Windows GDAL Auto-Discovery
if platform.system() == 'Windows':
    common_gdal_paths = [
        r'C:\OSGeo4W\bin',
        r'C:\OSGeo4W64\bin',
        r'C:\Program Files\GDAL',
    ]
    for path in common_gdal_paths:
        if os.path.exists(path):
            os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
            if not os.environ.get('GDAL_LIBRARY_PATH'):
                for f in os.listdir(path):
                    if f.startswith('gdal') and f.endswith('.dll'):
                        os.environ['GDAL_LIBRARY_PATH'] = os.path.join(path, f)
                        break
            if not os.environ.get('GEOS_LIBRARY_PATH'):
                for f in os.listdir(path):
                    if f.startswith('geos') and f.endswith('.dll'):
                        os.environ['GEOS_LIBRARY_PATH'] = os.path.join(path, f)
                        break
            break

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-ocean-intelligence-secret-key-12345')

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # PostGIS support
    'rest_framework',
    'corsheaders',
    
    # Custom apps
    'ocean',
    'fisheries',
    'biodiversity',
    'ai',
    'rag',
    'assistant',
    'simulation',
]

# Dynamic GDAL check to prevent startup crashes when GDAL is missing
try:
    from django.contrib.gis.gdal import HAS_GDAL
    if not HAS_GDAL:
        if 'django.contrib.gis' in INSTALLED_APPS:
            INSTALLED_APPS.remove('django.contrib.gis')
except Exception:
    if 'django.contrib.gis' in INSTALLED_APPS:
        INSTALLED_APPS.remove('django.contrib.gis')

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS at the top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration
# Support parsing DATABASE_URL like postgres://user:password@host:port/dbname
DATABASE_URL = os.getenv('DATABASE_URL', 'postgis://postgres:postgres@localhost:5432/ocean_intelligence')

# Fallback parser for DATABASE_URL
db_config = {}
if DATABASE_URL:
    import urllib.parse as urlparse
    url = urlparse.urlparse(DATABASE_URL)
    
    # Map scheme to Django's GIS backend
    backend = 'django.contrib.gis.db.backends.postgis'
    if url.scheme in ['postgres', 'postgresql']:
        backend = 'django.db.backends.postgresql'
    elif 'sqlite' in url.scheme:
        backend = 'django.db.backends.sqlite3'
        
    db_config = {
        'ENGINE': backend,
        'NAME': url.path[1:] if url.scheme != 'sqlite' else (url.path[2:] if url.path.startswith('//') else (url.path if url.path else 'db.sqlite3')),
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port or (5432 if backend != 'django.db.backends.sqlite3' else ''),
    }

DATABASES = {
    'default': db_config or {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'ocean_intelligence',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True  # For research/demo dashboard

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

# AI & LLM Settings
COPERNICUS_USERNAME = os.getenv('COPERNICUS_USERNAME')
COPERNICUS_PASSWORD = os.getenv('COPERNICUS_PASSWORD')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')  # gemini or openai
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-1.5-flash')

# Demo Mode toggle
DEMO_MODE = os.getenv('DEMO_MODE', 'True').lower() == 'true'
