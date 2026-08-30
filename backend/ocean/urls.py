from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ocean.views import RegionViewSet, OceanObservationViewSet

router = DefaultRouter()
router.register('regions', RegionViewSet, basename='region')
router.register('observations', OceanObservationViewSet, basename='observation')

urlpatterns = [
    path('', include(router.urls)),
]
