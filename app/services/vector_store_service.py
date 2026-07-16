from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings
from app.core.exceptions import ServiceException
from app.schemas.document import DocumentChunk, DocumentSearchResult


class VectorStoreService:
    """
    Store and search document chunks in ChromaDB.

    This service is responsible only for vector database operations.
    It should not extract PDFs, clean text, create chunks, or call an LLM.
    """

    def __init__(self, *, create_collection: bool = True) -> None:
        settings = get_settings()

        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = settings.chroma_collection_name

        persist_path = Path(self.persist_directory)
        if create_collection:
            persist_path.mkdir(parents=True, exist_ok=True)
        elif not persist_path.is_dir():
            raise ServiceException("Vector evidence storage is unavailable.")

        self.client = chromadb.PersistentClient(path=self.persist_directory)

        if create_collection:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self.collection = self.client.get_collection(name=self.collection_name)

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> int:
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ServiceException(
                "Chunk count and embedding count do not match."
            )

        ids = [self._build_chunk_id(chunk) for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [self._build_metadata(chunk) for chunk in chunks]

        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            return len(chunks)

        except Exception as exc:
            raise ServiceException("Failed to store chunks in ChromaDB.") from exc

    def search_similar_chunks(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[DocumentSearchResult]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise ServiceException("Failed to search ChromaDB collection.") from exc

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        search_results: list[DocumentSearchResult] = []

        for document_text, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}

            score = self._distance_to_similarity_score(distance)

            search_results.append(
                DocumentSearchResult(
                    document_id=str(metadata.get("document_id", "")),
                    filename=str(metadata.get("filename", "")),
                    page_number=int(metadata.get("page_number", 0)),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    section_title=metadata.get("section_title") or None,
                    text=document_text or "",
                    char_count=int(metadata.get("char_count", len(document_text or ""))),
                    score=score,
                )
            )

        return search_results

    def count_chunks(self) -> int:
        try:
            return self.collection.count()
        except Exception as exc:
            raise ServiceException("Failed to count ChromaDB chunks.") from exc

    def check_readiness(self) -> None:
        """Verify collection access without searching, embedding, or writing."""
        try:
            self.collection.count()
        except Exception as exc:
            raise ServiceException("Vector evidence storage is unavailable.") from exc

    def delete_document_chunks(self, document_id: str) -> None:
        """Compensate a partial ingestion without affecting other documents."""
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as exc:
            raise ServiceException(
                "Failed to clean up partially indexed document chunks."
            ) from exc

    def _build_chunk_id(self, chunk: DocumentChunk) -> str:
        return (
            f"{chunk.document_id}"
            f":page-{chunk.page_number}"
            f":chunk-{chunk.chunk_index}"
        )

    def _build_metadata(self, chunk: DocumentChunk) -> dict[str, Any]:
        return {
            "document_id": chunk.document_id,
            "filename": chunk.filename,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "section_title": chunk.section_title or "",
            "char_count": chunk.char_count,
        }

    def _distance_to_similarity_score(self, distance: float) -> float:
        """
        Chroma returns distance. Lower is better.
        With cosine distance, a simple readable score is 1 - distance.
        """

        score = 1.0 - float(distance)
        return round(max(0.0, min(1.0, score)), 4)
