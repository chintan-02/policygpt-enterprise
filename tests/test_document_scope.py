from uuid import uuid4

import chromadb

from app.services.vector_store_service import VectorStoreService


def test_document_scope_filters_before_top_k() -> None:
    store = VectorStoreService.__new__(VectorStoreService)
    store.collection = chromadb.EphemeralClient().create_collection(
        name=f"policy-scope-{uuid4()}"
    )
    standard_id, flexible_id = str(uuid4()), str(uuid4())
    store.collection.add(
        ids=["standard", "flexible"],
        embeddings=[[1.0, 0.0], [0.8, 0.2]],
        documents=["Remote work is allowed two days each week.",
                   "Remote work is allowed four days each week."],
        metadatas=[
            {"document_id": standard_id, "filename": "standard.pdf", "page_number": 1},
            {"document_id": flexible_id, "filename": "flexible.pdf", "page_number": 1},
        ],
    )

    unscoped = store.search_similar_chunks([1.0, 0.0], top_k=1)
    scoped = store.search_similar_chunks([1.0, 0.0], top_k=1, document_id=flexible_id)
    missing = store.search_similar_chunks([1.0, 0.0], top_k=1, document_id=str(uuid4()))

    assert [result.document_id for result in unscoped] == [standard_id]
    assert [result.document_id for result in scoped] == [flexible_id]
    assert "four days" in scoped[0].text
    assert missing == []
