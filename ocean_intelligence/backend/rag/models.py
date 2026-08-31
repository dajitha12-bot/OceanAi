import uuid
import json
from django.db import models

try:
    from pgvector.django import VectorField
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

class Document(models.Model):
    """Scientific papers, reports, guidelines for RAG context."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    """Chunks of documents for vector search."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    content = models.TextField()
    
    if HAS_PGVECTOR:
        # Standard dimension 768 (Gemini text-embedding-004)
        embedding = VectorField(dimensions=768, blank=True, null=True)
    else:
        embedding = models.TextField(blank=True, null=True, help_text="Stored as JSON array")
        
    created_at = models.DateTimeField(auto_now_add=True)

    def set_embedding(self, vector_list):
        if HAS_PGVECTOR:
            self.embedding = vector_list
        else:
            self.embedding = json.dumps(vector_list)

    def get_embedding(self):
        if not self.embedding:
            return []
        if HAS_PGVECTOR:
            return self.embedding
        return json.loads(self.embedding)

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"
