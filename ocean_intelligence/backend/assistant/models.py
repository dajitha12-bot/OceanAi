import uuid
from django.db import models

class ChatHistory(models.Model):
    """Stores conversational history of the AI Ocean Assistant sessions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True)
    role = models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name_plural = "Chat histories"

    def __str__(self):
        return f"{self.session_id[:8]} - {self.role}: {self.message[:30]}..."
