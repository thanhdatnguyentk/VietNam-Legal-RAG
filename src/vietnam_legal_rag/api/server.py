"""FastAPI REST API server for VietLegal RAG.

Exposes the RAG pipeline via HTTP endpoints for production deployment.

Run with:
    uvicorn vietnam_legal_rag.api.server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from vietnam_legal_rag.config import get_settings

logger = logging.getLogger(__name__)

# ── Global singletons (populated at startup) ──────────────────────────────

_retriever = None
_rag_pipeline = None


def _init_retriever():
    """Initialize the retriever stack once at startup."""
    global _retriever

    settings = get_settings()

    from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
    from vietnam_legal_rag.vectorstore.chroma import VectorStore
    from vietnam_legal_rag.retrieval.dense import DenseRetriever
    from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, HybridRetriever
    from vietnam_legal_rag.retrieval.graph import GraphEnhancedRetriever
    from vietnam_legal_rag.graph.neo4j_client import Neo4jClient

    logger.info("Loading embedder: %s on %s", settings.embedding_model, settings.embedding_device)
    embedder = VietnameseEmbedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )
    store = VectorStore()
    dense = DenseRetriever(embedder=embedder, store=store)

    bm25 = BM25Retriever()
    bm25._load()

    base_retriever = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        dense_weight=0.5,
        bm25_weight=0.5,
    )
    
    # Try to wrap with Knowledge Graph
    global _retriever
    try:
        neo4j_client = Neo4jClient()
        _retriever = GraphEnhancedRetriever(base_retriever=base_retriever, neo4j_client=neo4j_client)
        logger.info("Retriever initialized (Graph-Enhanced Hybrid)")
    except Exception as e:
        logger.warning(f"Could not initialize Neo4j client, falling back to Hybrid: {e}")
        _retriever = base_retriever
        logger.info("Retriever initialized (Hybrid: Dense=0.5, BM25=0.5)")


def _init_rag_pipeline():
    """Initialize the RAG pipeline with LLM."""
    global _rag_pipeline

    try:
        from vietnam_legal_rag.generation.llm import build_default_llm
        from vietnam_legal_rag.pipeline.rag import RAGPipeline

        llm = build_default_llm()
        _rag_pipeline = RAGPipeline(retriever=_retriever, llm=llm)
        logger.info("RAG pipeline initialized with LLM")
    except Exception as e:
        logger.warning("Could not initialize RAG pipeline (LLM may not be configured): %s", e)
        _rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("🏛️ VietLegal RAG API starting up...")
    _init_retriever()
    _init_rag_pipeline()
    logger.info("✅ Ready to serve requests.")
    yield
    logger.info("🛑 Shutting down...")


# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="VietLegal RAG API",
    description="Trợ lý ảo tư vấn pháp luật Việt Nam — powered by Hybrid Retrieval + IRAC CoT",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Câu hỏi pháp lý")
    top_k: int = Field(5, ge=1, le=20, description="Số kết quả trả về")
    domain: str | None = Field(None, description="Lọc theo lĩnh vực (ví dụ: giao_thong, dat_dai)")


class SearchHit(BaseModel):
    rank: int
    score: float
    document_number: str
    title: str
    article: str
    clause: str
    chapter: str
    text: str


class SearchResponse(BaseModel):
    query: str
    total_hits: int
    latency_ms: float
    hits: list[SearchHit]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Câu hỏi pháp lý")
    domain: str | None = Field(None, description="Lọc theo lĩnh vực")


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[str]
    latency_ms: float
    sources: list[SearchHit]


class HealthResponse(BaseModel):
    status: str
    retriever_ready: bool
    rag_ready: bool
    vector_count: int


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Kiểm tra trạng thái hệ thống."""
    from vietnam_legal_rag.vectorstore.chroma import VectorStore
    store = VectorStore()
    return HealthResponse(
        status="ok",
        retriever_ready=_retriever is not None,
        rag_ready=_rag_pipeline is not None,
        vector_count=store.count(),
    )


@app.post("/search", response_model=SearchResponse, tags=["Retrieval"])
async def search(req: SearchRequest):
    """Tìm kiếm văn bản pháp luật liên quan đến câu hỏi.

    Sử dụng Hybrid Retrieval (BM25 + Dense Semantic Search) để trả về
    các đoạn văn bản pháp luật có liên quan nhất.
    """
    if _retriever is None:
        raise HTTPException(status_code=503, detail="Retriever not initialized")

    t0 = time.perf_counter()
    hits = _retriever.retrieve(req.query, top_k=req.top_k, domain=req.domain)
    latency = (time.perf_counter() - t0) * 1000

    return SearchResponse(
        query=req.query,
        total_hits=len(hits),
        latency_ms=round(latency, 1),
        hits=[
            SearchHit(
                rank=hit.rank,
                score=round(hit.score, 6),
                document_number=hit.document.metadata.get("document_number", ""),
                title=hit.document.metadata.get("title", ""),
                article=hit.document.metadata.get("article", ""),
                clause=hit.document.metadata.get("clause", ""),
                chapter=hit.document.metadata.get("chapter", ""),
                text=hit.document.page_content[:500],
            )
            for hit in hits
        ],
    )


@app.post("/ask", response_model=AskResponse, tags=["RAG"])
async def ask(req: AskRequest):
    """Đặt câu hỏi pháp lý và nhận câu trả lời có trích dẫn.

    Sử dụng pipeline RAG đầy đủ: Hybrid Retrieval → IRAC CoT → LLM Generation.
    Yêu cầu cấu hình LLM (Gemini/OpenAI/Anthropic) trong file .env.
    """
    if _rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available. Configure LLM provider in .env"
        )

    t0 = time.perf_counter()
    answer = _rag_pipeline.query(req.question, domain=req.domain)
    latency = (time.perf_counter() - t0) * 1000

    return AskResponse(
        question=req.question,
        answer=answer.answer,
        citations=answer.citations,
        latency_ms=round(latency, 1),
        sources=[
            SearchHit(
                rank=hit.rank,
                score=round(hit.score, 6),
                document_number=hit.document.metadata.get("document_number", ""),
                title=hit.document.metadata.get("title", ""),
                article=hit.document.metadata.get("article", ""),
                clause=hit.document.metadata.get("clause", ""),
                chapter=hit.document.metadata.get("chapter", ""),
                text=hit.document.page_content[:500],
            )
            for hit in answer.hits
        ],
    )


@app.get("/domains", tags=["Metadata"])
async def list_domains():
    """Liệt kê các lĩnh vực pháp luật có trong hệ thống."""
    return {
        "domains": [
            {"id": "dan_su", "name": "Dân sự"},
            {"id": "dat_dai", "name": "Đất đai"},
            {"id": "doanh_nghiep", "name": "Doanh nghiệp"},
            {"id": "giao_duc", "name": "Giáo dục"},
            {"id": "giao_thong", "name": "Giao thông"},
            {"id": "hanh_chinh", "name": "Hành chính"},
            {"id": "hinh_su", "name": "Hình sự"},
            {"id": "lao_dong", "name": "Lao động"},
            {"id": "moi_truong", "name": "Môi trường"},
            {"id": "thue", "name": "Thuế"},
            {"id": "y_te", "name": "Y tế"},
            {"id": "khac", "name": "Khác"},
        ]
    }


# ── Static file serving (frontend) ───────────────────────────────────────

from pathlib import Path

_frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
if _frontend_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/app", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
    logger.info("Frontend mounted at /app from %s", _frontend_dir)

