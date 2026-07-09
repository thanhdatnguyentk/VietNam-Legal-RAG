# Vietnam Legal RAG

> Hệ thống **Retrieval-Augmented Generation (RAG) đa lĩnh vực** cho pháp luật Việt Nam.
> Skeleton + tài liệu — sẵn sàng cho giai đoạn triển khai tiếp theo.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![Status: Skeleton](https://img.shields.io/badge/status-skeleton-orange.svg)](docs/roadmap.md)

---

## 1. Giới thiệu

`vietnam-legal-rag` là bộ khung tham chiếu để xây dựng một **trợ lý ảo tư vấn
pháp luật Việt Nam** dựa trên công nghệ RAG hiện đại. Mục tiêu:

- **Chính xác**: mỗi câu trả lời phải trích dẫn đúng `Điều / Khoản / Điểm`.
- **Đa lĩnh vực**: cùng một pipeline phục vụ nhiều miền luật (giao thông, dân sự, hình sự, lao động, …).
- **Tái lập**: tất cả cấu hình đến từ biến môi trường, không hard-code.
- **Mở rộng**: thêm domain mới chỉ cần thêm 1 file vào `src/vietnam_legal_rag/domains/`.

Đây là giai đoạn **skeleton**: cấu trúc thư mục, interface, CLI scripts, tests, tài
liệu đã có. Logic ingest / retrieval / generation sẽ được viết ở các phase sau —
xem [`docs/roadmap.md`](docs/roadmap.md).

## 2. Kiến trúc tổng quan

```
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Scraper       │ → │ data/raw/      │   │  DomainSpec    │
│ (thư viện      │   │ (TXT + meta)   │   │  registry      │
│  pháp luật)    │   └───────┬────────┘   │  (multi-domain)│
└────────────────┘           │            └────────────────┘
                             ▼
                    ┌────────────────┐
                    │ Ingestion      │   chunk theo cấu trúc
                    │ loader+chunker │   Điều → Khoản → Điểm
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │ Embedding      │   keepitreal/vietnamese-sbert
                    │ (SBERT-VN)     │   hoặc multilingual-e5-large
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │ ChromaDB       │   persistent local index
                    │ vector store   │
                    └───────┬────────┘
                            ▼
            ┌───────────────┴────────────────┐
            ▼                                ▼
   ┌────────────────┐               ┌────────────────┐
   │ Dense retriever│               │ Hybrid retriever│  (BM25+dense)
   └───────┬────────┘               └───────┬────────┘
           └────────────────┬───────────────┘
                            ▼
                    ┌────────────────┐
                    │ RAG pipeline   │   system prompt tiếng Việt,
                    │ (LLM client)   │   IRAC + citation rules
                    └───────┬────────┘
                            ▼
                    ┌────────────────┐
                    │ CLI / API / UI │   scripts/query.py
                    └────────────────┘
```

Chi tiết hơn xem [`docs/architecture.md`](docs/architecture.md).

## 3. Yêu cầu

- **Python ≥ 3.10** (đã thử nghiệm trên 3.12).
- ~2 GB đĩa trống cho mô hình embedding tiếng Việt (SBERT ~250 MB, e5-large ~2.2 GB).
- (Tuỳ chọn) Docker nếu muốn nâng cấp lên Qdrant/Weaviate sau này.
- API key cho ít nhất một LLM provider (OpenAI hoặc Anthropic).

## 4. Cài đặt

```bash
# Clone & vào thư mục
git clone <repo-url> vietnam-legal-rag
cd vietnam-legal-rag

# (Khuyến nghị) tạo virtualenv
python -m venv .venv
source .venv/bin/activate

# Cài đặt chế độ phát triển (kèm dev dependencies cho test/lint)
make install-dev
```

> Nếu chưa có `make`, chạy thẳng: `pip install -e ".[dev]"`

## 5. Cấu hình

```bash
cp .env.example .env
# Mở .env và điền OPENAI_API_KEY hoặc ANTHROPIC_API_KEY
```

Các biến quan trọng (xem `.env.example` để biết đầy đủ):

| Biến                    | Mặc định                          | Ý nghĩa                                    |
|-------------------------|-----------------------------------|---------------------------------------------|
| `LLM_PROVIDER`          | `openai`                          | `openai` hoặc `anthropic`                  |
| `LLM_MODEL`             | `gpt-4o-mini`                     | Tên model                                  |
| `EMBEDDING_MODEL`       | `keepitreal/vietnamese-sbert`     | Model nhúng tiếng Việt                     |
| `EMBEDDING_DEVICE`      | `cpu`                             | `cpu` / `cuda` / `mps`                     |
| `CHROMA_PERSIST_DIR`    | `data/index`                      | Thư mục lưu index                          |
| `CHUNK_SIZE`            | `512`                             | Kích thước mỗi chunk                        |
| `CHUNK_OVERLAP`         | `64`                              | Độ chồng lấn                               |
| `RETRIEVAL_K`           | `5`                               | Top-k hits                                 |
| `SCRAPER_BASE_URL`      | `https://thuvienphapluat.vn`      | Domain nguồn scraping                      |

## 6. Quick start

> **Phase status:** Skeleton ✅ | Phase 2 (ingestion) ✅ | Phase 3+ (embed/retrieve/generate) ⏳
>
> `scripts/ingest.py` đã có implementation thật từ phase 2. Scraper + retrieval
> + generation vẫn là skeleton (raise `NotImplementedError` khi dùng).

```bash
# 6.1 Xem tất cả domain đã đăng ký
python scripts/scrape.py --help

# 6.2 (Đã có implementation phase 2) Ingest từ raw/ → processed/
python scripts/ingest.py --all --dry-run  # xem files sẽ xử lý, không ghi
python scripts/ingest.py --all --stats    # chạy thật + in per-file chunk count

# 6.3 (Đã có fixture test) Chạy nhanh với file luật mẫu trong repo:
python scripts/ingest.py \
  --raw-dir tests/fixtures \
  --out-dir /tmp/processed \
  --stats
ls /tmp/processed/

# 6.4 Phase sau (chưa implement, vẫn raise NotImplementedError):
make index
make query Q="Điều kiện cấp GPLX hạng B1?"
make eval
```

## 7. Cấu trúc thư mục

```
vietnam-legal-rag/
├── README.md                  ← bạn đang ở đây
├── pyproject.toml             ← khai báo package + dependencies
├── .env.example               ← template cho biến môi trường
├── Makefile                   ← shortcuts
│
├── data/                      ← bị git ignore (trừ .gitkeep)
│   ├── raw/                   ← output của scraper
│   ├── processed/             ← JSONL sau khi chunk
│   ├── eval/                  ← bộ câu hỏi + ground-truth
│   └── index/                 ← ChromaDB persistent
│
├── src/vietnam_legal_rag/
│   ├── config.py              ← pydantic Settings
│   ├── paths.py               ← đường dẫn tuyệt đối
│   ├── scrapers/              ← base + thuvienphapluat
│   ├── domains/               ← registry multi-domain
│   ├── ingestion/             ← loader, chunker, pipeline
│   ├── embeddings/            ← Vietnamese SBERT wrapper
│   ├── vectorstore/           ← ChromaDB wrapper
│   ├── retrieval/             ← dense + hybrid (BM25)
│   ├── generation/            ← LLM client + prompts
│   ├── pipeline/              ← end-to-end RAG
│   └── eval/                  ← evaluator
│
├── scripts/                   ← CLI (typer)
│   ├── scrape.py
│   ├── ingest.py
│   ├── build_index.py
│   ├── query.py
│   └── eval.py
│
├── tests/                     ← pytest
│   ├── test_smoke.py
│   ├── test_scrapers.py
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_pipeline.py
│
└── docs/
    ├── architecture.md
    ├── data-model.md
    ├── domains.md
    └── roadmap.md
```

## 8. Thêm một domain mới

Ví dụ thêm "Luật Đất đai":

```python
# src/vietnam_legal_rag/domains/dat_dai.py
from vietnam_legal_rag.domains.base import DomainSpec

DOMAIN = DomainSpec(
    name="dat_dai",
    display_name="Luật Đất đai 2024",
    description="Luật Đất đai 2024 (Luật số 31/2024/QH15).",
    source_urls=[],
    keywords=["đất đai", "quyền sử dụng đất", "thửa đất", "chuyển nhượng"],
)
```

```python
# src/vietnam_legal_rag/domains/__init__.py — thêm dòng
from vietnam_legal_rag.domains.dat_dai import DOMAIN as DAT_DAI
# ... và chèn DAT_DAI vào DOMAIN_REGISTRY
```

Không cần thay đổi bất kỳ file nào khác — registry sẽ tự nhặt domain mới.

## 9. Đóng góp

- Tuân thủ `ruff` (xem `make lint`).
- Mọi PR phải pass `make test`.
- Khi thêm module mới, đặt interface (abstract base) trước rồi mới đến implementation.
- Viết tiếng Việt trong docstring/prompt cho các phần liên quan UX người dùng Việt.

## 10. Giấy phép

MIT — xem [`LICENSE`](LICENSE). Văn bản pháp luật do scraper thu thập là tài
liệu công cộng của Nhà nước CHXHCN Việt Nam; giấy phép MIT chỉ áp dụng cho source
code trong repo này.
