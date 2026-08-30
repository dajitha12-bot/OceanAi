from django.urls import path, include
from rest_framework.routers import DefaultRouter
from fisheries.views import SpeciesViewSet, FisheriesOccurrenceViewSet, FisheriesIntelligenceViewSet

router = DefaultRouter()
router.register('species', SpeciesViewSet, basename='species')
router.register('occurrences', FisheriesOccurrenceViewSet, basename='occurrence')
router.register('intelligence', FisheriesIntelligenceViewSet, basename='intelligence')

urlpatterns = [
    path('', include(router.urls)),
]
