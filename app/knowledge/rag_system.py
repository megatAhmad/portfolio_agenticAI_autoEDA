"""RAG system for business context retrieval using ChromaDB."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available")


class Document(BaseModel):
    """A document chunk for the RAG system."""

    id: str
    content: str
    metadata: dict[str, Any] = {}
    source: str = ""


class RetrievalResult(BaseModel):
    """Result from a retrieval query."""

    documents: list[Document]
    query: str
    scores: list[float] = []


class RAGSystem:
    """RAG system for business context retrieval."""

    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    COLLECTION_NAME = "business_context"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        embedding_model: str = DEFAULT_MODEL,
    ):
        """Initialize RAG system.

        Args:
            persist_dir: Directory for ChromaDB persistence
            embedding_model: HuggingFace model for embeddings
        """
        self.persist_dir = persist_dir or Path("./chroma_db")
        self.embedding_model_name = embedding_model

        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._embedding_model: Optional[Any] = None

    def _get_client(self) -> Any:
        """Get or create ChromaDB client."""
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")

        if self._client is None:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self) -> Any:
        """Get or create the documents collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _get_embedding_model(self) -> Any:
        """Get or load the embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            )

        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
            chunk = " ".join(words[i : i + self.CHUNK_SIZE])
            if chunk.strip():
                chunks.append(chunk)

        return chunks if chunks else [text]

    def _generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for a document chunk.

        Args:
            content: Document content
            source: Document source

        Returns:
            Unique ID string
        """
        hash_input = f"{source}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def add_document(
        self,
        content: str,
        source: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """Add a document to the RAG system.

        Args:
            content: Document content
            source: Source identifier (filename, URL, etc.)
            metadata: Additional metadata

        Returns:
            List of chunk IDs
        """
        collection = self._get_collection()
        model = self._get_embedding_model()

        chunks = self._chunk_text(content)
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = self._generate_id(chunk, f"{source}_{i}")
            ids.append(chunk_id)
            documents.append(chunk)

            chunk_metadata = {
                "source": source,
                "chunk_index": i,
                "total_chunks": len(chunks),
                **(metadata or {}),
            }
            metadatas.append(chunk_metadata)

            # Generate embedding
            embedding = model.encode(chunk).tolist()
            embeddings.append(embedding)

        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks from {source}")
        return ids

    def add_json_context(
        self,
        json_path: Path,
        source_name: Optional[str] = None,
    ) -> list[str]:
        """Add context from a JSON file.

        Args:
            json_path: Path to JSON file
            source_name: Optional source name override

        Returns:
            List of chunk IDs
        """
        with open(json_path) as f:
            data = json.load(f)

        source = source_name or json_path.name

        # Convert JSON to readable text
        content_parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    content_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            item_text = ", ".join(
                                f"{k}: {v}" for k, v in item.items()
                                if isinstance(v, (str, int, float))
                            )
                            content_parts.append(f"{key} - {item_text}")
                        else:
                            content_parts.append(f"{key}: {item}")

        content = "\n".join(content_parts)
        return self.add_document(content, source, {"type": "json"})

    def add_text_context(
        self,
        text_path: Path,
        source_name: Optional[str] = None,
    ) -> list[str]:
        """Add context from a text file.

        Args:
            text_path: Path to text file
            source_name: Optional source name override

        Returns:
            List of chunk IDs
        """
        with open(text_path) as f:
            content = f.read()

        source = source_name or text_path.name
        return self.add_document(content, source, {"type": "text"})

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> RetrievalResult:
        """Retrieve relevant documents for a query.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            RetrievalResult with matching documents
        """
        collection = self._get_collection()
        model = self._get_embedding_model()

        # Generate query embedding
        query_embedding = model.encode(query).tolist()

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        documents = []
        scores = []

        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                doc_id = results["ids"][0][i] if results["ids"] else f"doc_{i}"

                documents.append(Document(
                    id=doc_id,
                    content=doc,
                    metadata=metadata,
                    source=metadata.get("source", ""),
                ))

                # Convert distance to similarity score (cosine)
                if results["distances"] and results["distances"][0]:
                    distance = results["distances"][0][i]
                    scores.append(1 - distance)  # Convert distance to similarity

        return RetrievalResult(
            documents=documents,
            query=query,
            scores=scores,
        )

    def get_context_for_query(
        self,
        query: str,
        n_results: int = 3,
    ) -> str:
        """Get formatted context string for LLM prompt.

        Args:
            query: User query
            n_results: Number of context chunks to retrieve

        Returns:
            Formatted context string
        """
        results = self.retrieve(query, n_results)

        if not results.documents:
            return "No relevant business context found."

        context_parts = ["Relevant Business Context:"]
        for i, doc in enumerate(results.documents, 1):
            score = results.scores[i - 1] if results.scores else 0
            context_parts.append(f"\n[{i}] (relevance: {score:.2f})")
            context_parts.append(doc.content)
            if doc.source:
                context_parts.append(f"Source: {doc.source}")

        return "\n".join(context_parts)

    def delete_source(self, source: str) -> int:
        """Delete all documents from a source.

        Args:
            source: Source identifier

        Returns:
            Number of documents deleted
        """
        collection = self._get_collection()

        # Get IDs for this source
        results = collection.get(
            where={"source": source},
            include=[],
        )

        if results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks from {source}")
            return len(results["ids"])

        return 0

    def list_sources(self) -> list[str]:
        """List all unique sources in the collection.

        Returns:
            List of source names
        """
        collection = self._get_collection()

        # Get all documents with metadata
        results = collection.get(include=["metadatas"])

        sources = set()
        if results["metadatas"]:
            for metadata in results["metadatas"]:
                if metadata and "source" in metadata:
                    sources.add(metadata["source"])

        return sorted(sources)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the RAG system.

        Returns:
            Dictionary with stats
        """
        collection = self._get_collection()
        count = collection.count()

        sources = self.list_sources()

        return {
            "total_chunks": count,
            "num_sources": len(sources),
            "sources": sources,
            "embedding_model": self.embedding_model_name,
            "persist_dir": str(self.persist_dir),
        }

    def clear(self) -> None:
        """Clear all documents from the collection."""
        client = self._get_client()
        client.delete_collection(self.COLLECTION_NAME)
        self._collection = None
        logger.info("Cleared RAG collection")
