from django.urls import path, include
from rest_framework.routers import DefaultRouter
from biodiversity.views import BiodiversityIndicatorViewSet

router = DefaultRouter()
router.register('indicators', BiodiversityIndicatorViewSet, basename='indicator')

urlpatterns = [
    path('', include(router.urls)),
]
