"""
Document ingestion pipeline.
Loads policy documents, chunks them, and prepares for embedding and storage.
"""

import os
import glob
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentLoader:
    """Load and chunk policy documents from the data/policies directory."""

    def __init__(self, policies_dir: str, chunk_size: int = 800, chunk_overlap: int = 200):
        """
        Initialize the document loader.

        Args:
            policies_dir: Path to the directory containing policy markdown files
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.policies_dir = policies_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )

    def load_documents(self) -> list[Document]:
        """
        Load all markdown policy files from the policies directory.

        Returns:
            List of LangChain Document objects with metadata.
        """
        documents = []
        pattern = os.path.join(self.policies_dir, "*.md")
        files = sorted(glob.glob(pattern))

        if not files:
            raise FileNotFoundError(
                f"No markdown files found in {self.policies_dir}. "
                "Please add policy documents as .md files."
            )

        for filepath in files:
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract document metadata from the content
            doc_id = self._extract_field(content, "Document ID:")
            title = self._extract_title(content)

            doc = Document(
                page_content=content,
                metadata={
                    "source": filename,
                    "doc_id": doc_id,
                    "title": title,
                    "filepath": filepath,
                },
            )
            documents.append(doc)

        print(f"Loaded {len(documents)} policy documents from {self.policies_dir}")
        return documents

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """
        Split documents into smaller chunks for embedding.

        Uses a hierarchical splitting strategy:
        - First tries to split on section headers (## , ### )
        - Then paragraphs (\\n\\n)
        - Then sentences (. )
        - Finally, at character level as a last resort

        Args:
            documents: List of full documents to chunk

        Returns:
            List of chunked Document objects with preserved metadata.
        """
        chunks = []

        for doc in documents:
            doc_chunks = self.text_splitter.split_documents([doc])

            # Add chunk index and section info to metadata
            for i, chunk in enumerate(doc_chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(doc_chunks)
                chunk.metadata["section"] = self._extract_section_header(chunk.page_content)

                # Create a citation-friendly identifier
                source = chunk.metadata.get("source", "unknown")
                section = chunk.metadata.get("section", "")
                chunk.metadata["citation"] = f"{source} — {section}" if section else source

            chunks.extend(doc_chunks)

        print(
            f"Split {len(documents)} documents into {len(chunks)} chunks "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks

    def load_and_chunk(self) -> list[Document]:
        """
        Convenience method: load documents and chunk them in one call.

        Returns:
            List of chunked Document objects ready for embedding.
        """
        documents = self.load_documents()
        return self.chunk_documents(documents)

    @staticmethod
    def _extract_field(content: str, field_name: str) -> str:
        """Extract a metadata field value from document content."""
        for line in content.split("\n"):
            if field_name in line:
                return line.split(field_name)[-1].strip().strip("*")
        return ""

    @staticmethod
    def _extract_title(content: str) -> str:
        """Extract the document title (first # heading)."""
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return stripped[2:].strip()
        return "Untitled Policy"

    @staticmethod
    def _extract_section_header(chunk_text: str) -> str:
        """Extract the most relevant section header from a chunk."""
        lines = chunk_text.split("\n")
        # Look for the most specific heading (### before ##)
        best_header = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("### "):
                best_header = stripped.replace("### ", "").strip()
            elif stripped.startswith("## ") and not best_header:
                best_header = stripped.replace("## ", "").strip()
        return best_header
