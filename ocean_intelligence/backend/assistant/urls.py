from django.urls import path, include
from rest_framework.routers import DefaultRouter
from assistant.views import ChatHistoryViewSet, ChatAssistantView

router = DefaultRouter()
router.register('history', ChatHistoryViewSet, basename='history')

urlpatterns = [
    path('chat/', ChatAssistantView.as_view(), name='chat'),
    path('', include(router.urls)),
]
