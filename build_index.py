"""
Build script — Initialize the vector store from policy documents.
Run this before using the application or evaluating.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from src.ingestion.document_loader import DocumentLoader
from src.vectorstore.store import PolicyVectorStore


def build():
    """Build the FAISS vector store from policy documents."""
    print("=" * 60)
    print("  The Platform Policy Vector Store Builder")
    print("=" * 60)
    print()

    # Validate
    settings.validate()

    # Load and chunk documents
    loader = DocumentLoader(
        policies_dir=settings.POLICIES_DIR,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    chunks = loader.load_and_chunk()

    # Count total words
    total_words = sum(len(c.page_content.split()) for c in chunks)
    print(f"Total words across all chunks: {total_words:,}")

    # Build vector store
    store = PolicyVectorStore(
        embedding_model=settings.EMBEDDING_MODEL,
        store_path=settings.VECTOR_STORE_PATH,
    )
    store.build_index(chunks)
    store.save()

    # Quick test
    print("\nQuick search test: 'return policy for damaged items'")
    results = store.search("return policy for damaged items", k=3)
    for i, doc in enumerate(results, 1):
        print(f"  {i}. [{doc.metadata.get('citation', 'N/A')}] — score: {doc.metadata.get('relevance_score', 0):.3f}")

    print("\nVector store built successfully!")
    print(f"   Location: {settings.VECTOR_STORE_PATH}")


if __name__ == "__main__":
    build()
