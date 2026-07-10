"""Retrieval tests for Dense and BM25 retrievers."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.documents import Document

from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, HybridRetriever


def test_retrieval_hit_dataclass() -> None:
    doc = Document(page_content="Test", metadata={"chunk_id": "123"})
    hit = RetrievalHit(document=doc, score=0.9, rank=1)
    assert hit.score == 0.9
    assert hit.rank == 1
    assert hit.document.page_content == "Test"


def test_dense_retriever() -> None:
    # Mocks
    mock_embedder = MagicMock()
    mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]
    
    mock_store = MagicMock()
    mock_store.query.return_value = [
        {"id": "c1", "document": "Doc 1", "metadata": {"domain": "thue"}, "distance": 0.1},
        {"id": "c2", "document": "Doc 2", "metadata": {"domain": "thue"}, "distance": 0.2},
    ]

    retriever = DenseRetriever(embedder=mock_embedder, store=mock_store, top_k=2)
    hits = retriever.retrieve("Luật thuế", domain="thue")

    assert len(hits) == 2
    assert hits[0].score == 0.9  # 1 - 0.1
    assert hits[1].score == 0.8  # 1 - 0.2
    assert hits[0].document.page_content == "Doc 1"
    
    mock_embedder.embed_query.assert_called_once_with("Luật thuế")
    mock_store.query.assert_called_once_with(
        query_embedding=[0.1, 0.2, 0.3],
        top_k=2,
        where={"domain": "thue"}
    )


def test_bm25_retriever() -> None:
    retriever = BM25Retriever()
    
    # Mock data
    doc1 = Document(page_content="Luật giao thông đường bộ", metadata={"domain": "giao_thong"})
    doc2 = Document(page_content="Luật doanh nghiệp", metadata={"domain": "doanh_nghiep"})
    
    retriever._documents = [doc1, doc2]
    
    # Inject fake BM25Okapi index directly
    mock_index = MagicMock()
    mock_index.get_scores.return_value = [1.5, 0.1]
    retriever._index = mock_index
    retriever._loaded = True
    
    # Retrieve without domain
    hits = retriever.retrieve("giao thông")
    assert len(hits) == 2
    assert hits[0].document.page_content == "Luật giao thông đường bộ"
    
    # Retrieve with domain filter
    hits = retriever.retrieve("giao thông", domain="doanh_nghiep")
    assert len(hits) == 1
    assert hits[0].document.page_content == "Luật doanh nghiệp"


def test_hybrid_retriever() -> None:
    # Setup mocks returning hits
    hit1 = RetrievalHit(Document(page_content="D1", metadata={"chunk_id": "1"}), score=0.9, rank=1)
    hit2 = RetrievalHit(Document(page_content="D2", metadata={"chunk_id": "2"}), score=0.8, rank=2)
    hit3 = RetrievalHit(Document(page_content="D3", metadata={"chunk_id": "3"}), score=0.7, rank=1)
    
    mock_dense = MagicMock()
    mock_dense.retrieve.return_value = [hit1, hit2]  # Ranks 1 and 2
    
    mock_bm25 = MagicMock()
    mock_bm25.retrieve.return_value = [hit2, hit3]  # Ranks 1 and 2
    
    # Init hybrid
    hybrid = HybridRetriever(
        dense_retriever=mock_dense,
        bm25_retriever=mock_bm25,
        dense_weight=0.5,
        bm25_weight=0.5,
        rrf_k=60
    )
    
    hits = hybrid.retrieve("test query", top_k=3)
    
    assert len(hits) == 3
    
    # Calculate expected RRF
    # hit1 (chunk 1): dense rank 1 -> 0.5 / 61 = 0.00819
    # hit2 (chunk 2): dense rank 2 -> 0.5 / 62 = 0.00806 + bm25 rank 1 -> 0.5 / 61 = 0.00819 -> Total: 0.01626
    # hit3 (chunk 3): bm25 rank 2 -> 0.5 / 62 = 0.00806
    
    # So hit2 should be rank 1
    assert hits[0].document.metadata["chunk_id"] == "2"
    assert hits[1].document.metadata["chunk_id"] == "1"
    assert hits[2].document.metadata["chunk_id"] == "3"
