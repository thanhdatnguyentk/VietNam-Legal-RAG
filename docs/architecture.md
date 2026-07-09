# Architecture

## Pipeline tổng quan

```
[Scraper]  →  data/raw/  →  [Loader]  →  [Chunker]  →  data/processed/  →
[Embedder]  →  [ChromaDB]  →  [Retriever]  →  [LLM]  →  [Answer + citations]
```

Mỗi bước được tách thành một module riêng với interface (abstract base) để có thể:

1. **Thay thế độc lập** — đổi từ ChromaDB sang Qdrant không ảnh hưởng retrieval.
2. **Test cô lập** — mỗi module có test riêng với mock khi cần.
3. **Mở rộng domain** — chỉ cần đăng ký `DomainSpec` mới.

## Các lớp kiến trúc

### 1. Data layer (`scrapers/`, `ingestion/`, `domains/`)
- **Scrapers**: lấy HTML/TXT từ nguồn web → ghi `data/raw/<domain>/<số hiệu>.txt` kèm sidecar `.meta.json`.
- **Loader**: đọc file TXT → list[Document] của LangChain.
- **Chunker**: tách theo cấu trúc **Điều → Khoản → Điểm** để giữ nguyên mạch pháp lý.
- **Domain registry**: tra cứu nhanh spec của từng miền luật.

### 2. Vector layer (`embeddings/`, `vectorstore/`, `retrieval/`)
- **Embedder**: SBERT tiếng Việt; tùy chọn multilingual-e5-large.
- **Vector store**: ChromaDB persistent (DuckDB+Parquet backend).
- **Retriever**: hiện có `DenseRetriever`; `HybridRetriever` (BM25 + dense) sẽ thêm ở phase sau.

### 3. Generation layer (`generation/`, `pipeline/`)
- **LLM client**: interface `LLMClient`; concrete sẽ wrap `ChatOpenAI` / `ChatAnthropic`.
- **Prompts**: tiếng Việt, có quy tắc citation bắt buộc + IRAC structure.
- **RAGPipeline**: nhận `question` → trả `RAGAnswer` (answer + citations + hits).

### 4. Eval & CLI (`eval/`, `scripts/`)
- **Evaluator**: precision@k, recall@k, faithfulness.
- **CLI**: `typer` + `rich` để có output đẹp.

## Lựa chọn công nghệ & trade-offs

| Quyết định                          | Lý do                                                                | Thay thế khả dĩ                |
|--------------------------------------|----------------------------------------------------------------------|--------------------------------|
| **ChromaDB persistent local**        | Đơn giản, không cần Docker, persist OK với ~100k chunks.            | Qdrant (Docker)                |
| **Vietnamese SBERT (`keepitreal/…`)** | ~250 MB, chạy CPU ổn, recall tốt cho tiếng Việt phổ thông.        | `bkai-foundation-models/…`, `intfloat/multilingual-e5-large` |
| **LangChain ≥ 0.2**                  | Hệ sinh thái lớn, cộng đồng đông, dễ swap provider.                 | LlamaIndex (gọn hơn cho RAG đơn giản) |
| **Structural chunking**              | Tránh đứt gãy cấu trúc Điều–Khoản–Điểm.                           | Recursive splitter (default)   |
| **Dense retrieval trước**            | Đủ tốt cho MVP; nâng cấp hybrid sau.                                | Hybrid BM25+dense ngay từ đầu  |
| **Pydantic Settings**                | Validate config tại startup, load từ .env, IDE-friendly.            | `dynaconf`, `hydra`            |
| **Typer + Rich CLI**                 | Type-hint CLI + output có màu, đẹp hơn `argparse`.                  | `argparse`, `click`            |

## Schema dữ liệu

Xem [`data-model.md`](data-model.md) để biết chi tiết trường `RawDocument`,
processed chunk, và metadata trong ChromaDB.

## Đa tác nhân (multi-agent) — phase tương lai

Hệ thống sẽ tiến tới kiến trúc **agentic RAG** với:

- **Router Agent**: phân loại câu hỏi → chọn domain.
- **Statutory Agent / Case Law Agent / Compliance Agent**: chuyên biệt theo miền.
- **MCP Server**: tập trung hoá tool (vector search, graph query, web search).

Hiện tại, repository đặt nền tảng (registry + interfaces) để việc thêm agent ở
phase sau là một thay đổi **additive**, không phải rewrite.

## Sequence diagram — happy path

```
User       CLI          Pipeline      Retriever    VectorStore   LLM
 │         query()       │              │             │           │
 │─────────▶│             │              │             │           │
 │          │   query()   │              │             │           │
 │          │────────────▶│              │             │           │
 │          │             │   embed()    │             │           │
 │          │             │───────────────────────────▶│           │
 │          │             │   query()    │             │           │
 │          │             │─────────────▶│             │           │
 │          │             │              │  search()   │           │
 │          │             │              │────────────▶│           │
 │          │             │              │  hits[]     │           │
 │          │             │              │◀────────────│           │
 │          │             │  hits[]      │             │           │
 │          │             │◀─────────────│             │           │
 │          │             │                          generate()   │
 │          │             │───────────────────────────────────────▶
 │          │             │                          answer       │
 │          │             │◀───────────────────────────────────────
 │          │ RAGAnswer   │              │             │           │
 │          │◀────────────│              │             │           │
 │   print  │             │              │             │           │
 │◀─────────│             │              │             │           │
```
