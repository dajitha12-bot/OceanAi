from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views from apps
from ocean.views import MapLayersView, OceanObservationViewSet, RegionViewSet
from fisheries.views import SpeciesViewSet, FisheriesOccurrenceViewSet, FisheriesIntelligenceViewSet
from biodiversity.views import BiodiversityIndicatorViewSet
from ai.views import AnomalyViewSet, AIPredictionViewSet, AIInsightsViewSet

# Global router for root-level endpoints
router = DefaultRouter()
router.register('ocean/observations', OceanObservationViewSet, basename='obs')
router.register('species', SpeciesViewSet, basename='spec')
router.register('anomalies', AnomalyViewSet, basename='anom')
router.register('predictions', AIPredictionViewSet, basename='pred')
router.register('insights', AIInsightsViewSet, basename='ins')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root API routers
    path('api/', include(router.urls)),
    
    # Combined map layers GeoJSON API
    path('api/map/', MapLayersView.as_view(), name='map-layers'),
    
    # App-specific namespaces (for fallback and detail endpoints)
    path('api/ocean/', include('ocean.urls')),
    path('api/fisheries/', include('fisheries.urls')),
    path('api/biodiversity/', include('biodiversity.urls')),
    path('api/simulation/', include('simulation.urls')),
    path('api/assistant/', include('assistant.urls')),
]
