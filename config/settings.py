"""
Configuration settings for the E-commerce Support Resolution Agent.
Loads environment variables and provides centralized config access.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized configuration for the application."""

    # Groq (Primary LLM Provider)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Google Gemini (Fallback)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Models
    LLM_MODEL: str = os.getenv("LLM_MODEL", "groq/llama-3.1-8b-instant")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Paths
    POLICIES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "policies")
    VECTOR_STORE_PATH: str = os.getenv(
        "VECTOR_STORE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vectorstore_hf"),
    )

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # Retriever
    RETRIEVER_K: int = int(os.getenv("RETRIEVER_K", "3"))

    @classmethod
    def validate(cls) -> None:
        """Validate that at least one API Key is present."""
        if not cls.GROQ_API_KEY and not cls.GOOGLE_API_KEY:
            raise ValueError(
                "Neither GROQ_API_KEY nor GOOGLE_API_KEY is set. Please set one in your .env file."
            )


settings = Settings()
