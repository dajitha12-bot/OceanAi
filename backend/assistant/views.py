from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from assistant.models import ChatHistory
from assistant.chat_agent import query_llm_assistant
from rest_framework.serializers import ModelSerializer

class ChatHistorySerializer(ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id', 'session_id', 'role', 'message', 'timestamp']


class ChatHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatHistory.objects.all()
    serializer_class = ChatHistorySerializer
    
    def get_queryset(self):
        session_id = self.request.query_params.get('session_id')
        if session_id:
            return self.queryset.filter(session_id=session_id).order_by('timestamp')
        return self.queryset.none()


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class ChatAssistantView(APIView):
    """Conversational endpoint interfacing user query to LLM+RAG+DB workflow."""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        message = request.data.get('message')
        session_id = request.data.get('session_id', 'default-session')
        
        if not message:
            return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Log User Message safely
        try:
            ChatHistory.objects.create(
                session_id=session_id,
                role='user',
                message=message
            )
        except Exception:
            pass
        
        # 2. Run Assistant Query
        response_text = query_llm_assistant(message) or "I analyzed the ocean intelligence database, but could not produce a response. Please try rephrasing your question."
        
        # 3. Log Assistant Response safely
        try:
            ChatHistory.objects.create(
                session_id=session_id,
                role='assistant',
                message=response_text
            )
        except Exception:
            pass
        
        # Return chat payload
        return Response({
            'message': response_text,
            'session_id': session_id,
            'role': 'assistant'
        }, status=status.HTTP_200_OK)
