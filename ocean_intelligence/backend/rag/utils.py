import json
import random
import hashlib
from django.conf import settings

def chunk_text(text, chunk_size=800, overlap=100):
    """Splits text into chunks of chunk_size characters with overlap."""
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += (chunk_size - overlap)
        
    return chunks


def get_embedding(text, provider=None, api_key=None, model=None):
    """
    Generates embedding vector. 
    If api_key is missing or in Demo Mode, falls back to deterministic mock vector.
    """
    prov = provider or getattr(settings, 'LLM_PROVIDER', 'gemini')
    key = api_key or getattr(settings, 'LLM_API_KEY', None)
    mdl = model or getattr(settings, 'LLM_MODEL', 'gemini-1.5-flash')
    
    is_demo = getattr(settings, 'DEMO_MODE', True)
    
    if is_demo or not key:
        return get_mock_embedding(text)
        
    try:
        if prov == 'gemini':
            # Use google-genai client
            from google import genai
            client = genai.Client(api_key=key)
            # text-embedding-004 is standard Gemini embedding model
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            # return float list
            return response.embeddings[0].values
            
        elif prov == 'openai':
            from openai import OpenAI
            client = OpenAI(api_key=key)
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
            
    except Exception as e:
        # Fallback to mock on error to maintain app stability
        print(f"Embedding API Error: {e}. Falling back to deterministic mock embeddings.")
        return get_mock_embedding(text)

    return get_mock_embedding(text)


def get_mock_embedding(text, dimension=768):
    """
    Generates a deterministic float vector based on SHA-256 hash of the input text.
    Ensures that identical queries yield identical vectors for local cosine search.
    """
    # Create seed from text hash
    sha = hashlib.sha256(text.encode('utf-8')).digest()
    seed = int.from_bytes(sha, byteorder='big') % (2**32)
    
    rnd = random.Random(seed)
    vector = [rnd.uniform(-1.0, 1.0) for _ in range(dimension)]
    
    # L2 normalize
    norm = sum(x**2 for x in vector)**0.5
    if norm > 0:
        vector = [x / norm for x in vector]
    else:
        vector = [0.0] * dimension
        vector[0] = 1.0
        
    return vector
