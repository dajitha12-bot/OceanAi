from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ai.views import AnomalyViewSet, AIPredictionViewSet, AIInsightsViewSet

router = DefaultRouter()
router.register('anomalies', AnomalyViewSet, basename='anomaly')
router.register('predictions', AIPredictionViewSet, basename='prediction')
router.register('insights', AIInsightsViewSet, basename='insight')

urlpatterns = [
    path('', include(router.urls)),
]
