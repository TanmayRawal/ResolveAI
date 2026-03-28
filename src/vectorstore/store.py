"""
Vector store management using FAISS.
Handles embedding, storing, and retrieving policy document chunks.
"""

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


class PolicyVectorStore:
    """Manages the FAISS vector store for policy documents."""

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        store_path: str = "./data/vectorstore_hf",
    ):
        """
        Initialize the vector store using local HuggingFace embeddings.

        Args:
            embedding_model: HuggingFace model name
            store_path: Path to save/load the FAISS index
        """
        self.store_path = store_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
        )
        self.vectorstore: FAISS | None = None

    def build_index(self, chunks: list[Document]) -> FAISS:
        """
        Build a FAISS index from document chunks.

        Args:
            chunks: List of Document objects to embed and store

        Returns:
            The built FAISS vector store
        """
        print(f"Building FAISS index from {len(chunks)} chunks...")

        self.vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings,
        )

        print(f"FAISS index built with {len(chunks)} vectors")
        return self.vectorstore

    def save(self) -> None:
        """Save the FAISS index to disk."""
        if self.vectorstore is None:
            raise ValueError("No vector store to save. Build the index first.")

        os.makedirs(self.store_path, exist_ok=True)
        self.vectorstore.save_local(self.store_path)
        print(f"Vector store saved to {self.store_path}")

    def load(self) -> FAISS:
        """
        Load a previously saved FAISS index from disk.

        Returns:
            The loaded FAISS vector store
        """
        if not os.path.exists(self.store_path):
            raise FileNotFoundError(
                f"No vector store found at {self.store_path}. "
                "Run build_index() first."
            )

        self.vectorstore = FAISS.load_local(
            self.store_path,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )
        print(f"Vector store loaded from {self.store_path}")
        return self.vectorstore

    def search(self, query: str, k: int = 5) -> list[Document]:
        """
        Search for relevant policy chunks.

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of relevant Document objects with scores
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Build or load the index first.")

        results = self.vectorstore.similarity_search_with_score(query, k=k)

        documents = []
        for doc, score in results:
            doc.metadata["relevance_score"] = round(1 - score, 4)  # Convert distance to similarity
            documents.append(doc)

        return documents

    def search_with_multiple_queries(self, queries: list[str], k: int = 3) -> list[Document]:
        """
        Search with multiple queries and deduplicate results.

        Args:
            queries: List of search queries
            k: Number of results per query

        Returns:
            Deduplicated list of relevant Document objects
        """
        all_results = {}

        for query in queries:
            results = self.search(query, k=k)
            for doc in results:
                # Use content hash as dedup key
                key = hash(doc.page_content[:200])
                if key not in all_results:
                    all_results[key] = doc
                else:
                    # Keep the higher relevance score
                    existing_score = all_results[key].metadata.get("relevance_score", 0)
                    new_score = doc.metadata.get("relevance_score", 0)
                    if new_score > existing_score:
                        all_results[key] = doc

        # Sort by relevance score descending
        sorted_results = sorted(
            all_results.values(),
            key=lambda d: d.metadata.get("relevance_score", 0),
            reverse=True,
        )

        return sorted_results

    def get_retriever(self, k: int = 5):
        """
        Get a LangChain retriever interface for the vector store.

        Args:
            k: Number of documents to retrieve

        Returns:
            LangChain retriever object
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Build or load the index first.")

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )
