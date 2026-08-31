import os
from django.core.management.base import BaseCommand
from django.db import transaction
from rag.models import Document, DocumentChunk
from rag.utils import chunk_text, get_embedding

try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

class Command(BaseCommand):
    help = "Ingest PDF and Text research papers/reports into pgvector RAG store."

    def add_arguments(self, parser):
        parser.add_argument('--dir', type=str, help="Custom directory containing PDFs/Text files.")
        parser.add_argument('--chunk-size', type=int, default=800, help="Character chunk size.")
        parser.add_argument('--overlap', type=int, default=100, help="Chunk character overlap.")

    def handle(self, *args, **options):
        custom_dir = options['dir']
        chunk_size = options['chunk_size']
        overlap = options['overlap']

        # Determine paper directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        default_dir = os.path.join(base_dir, 'data', 'scientific_papers')
        
        target_dir = custom_dir if custom_dir else default_dir
        
        if not os.path.exists(target_dir):
            self.stderr.write(f"Scientific papers directory not found at: {target_dir}")
            return
            
        self.stdout.write(f"Scanning for research papers in: {target_dir}")
        
        files = [f for f in os.listdir(target_dir) if f.endswith(('.txt', '.pdf'))]
        if not files:
            self.stdout.write("No text or PDF papers found.")
            return

        for filename in files:
            filepath = os.path.join(target_dir, filename)
            self.stdout.write(f"Processing document: {filename}...")
            
            text_content = ""
            if filename.endswith('.txt'):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                except Exception as e:
                    self.stderr.write(f"Failed to read text file {filename}: {e}")
                    continue
            elif filename.endswith('.pdf'):
                if not HAS_PYPDF:
                    self.stderr.write(f"PyPDF2 package not available. Skipping PDF file {filename}.")
                    continue
                try:
                    with open(filepath, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages:
                            text_content += (page.extract_text() or "") + "\n"
                except Exception as e:
                    self.stderr.write(f"Failed to extract PDF text from {filename}: {e}")
                    continue
                    
            if not text_content.strip():
                self.stdout.write(f"Document {filename} has empty content. Skipping.")
                continue
                
            # Database storage
            with transaction.atomic():
                # Delete existing of same name to avoid duplicates
                Document.objects.filter(file_name=filename).delete()
                
                doc = Document.objects.create(
                    title=filename.replace('.txt', '').replace('.pdf', '').replace('_', ' ').title(),
                    file_name=filename
                )
                
                chunks = chunk_text(text_content, chunk_size, overlap)
                self.stdout.write(f"Split {filename} into {len(chunks)} chunks. Generating embeddings...")
                
                for idx, chunk in enumerate(chunks):
                    # Compute embedding vector (list of floats)
                    vector = get_embedding(chunk)
                    
                    chunk_obj = DocumentChunk(
                        document=doc,
                        chunk_index=idx,
                        content=chunk
                    )
                    # Use model helper to assign vector (handles pgvector vector type or text fallback)
                    chunk_obj.set_embedding(vector)
                    chunk_obj.save()
                    
            self.stdout.write(self.style.SUCCESS(f"Successfully ingested {filename} ({len(chunks)} chunks)."))
