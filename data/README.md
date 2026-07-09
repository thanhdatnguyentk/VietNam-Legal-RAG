# Thư mục `data/`

Toàn bộ thư mục `data/*` bị `.gitignore` trừ `.gitkeep` để giữ structure.

| Thư mục         | Sinh ra bởi         | Vai trò                                                          |
|-----------------|---------------------|------------------------------------------------------------------|
| `data/raw/`     | `scripts/scrape.py` | Văn bản pháp luật thô (TXT) + sidecar `.meta.json` theo domain. |
| `data/processed/` | `scripts/ingest.py` | JSONL chunks, mỗi dòng `{text, metadata}` cho mỗi domain.       |
| `data/eval/`    | (thủ công)          | JSONL câu hỏi + ground-truth để chạy `scripts/eval.py`.          |
| `data/index/`   | `scripts/build_index.py` | ChromaDB persistent storage (DuckDB+Parquet backend).     |

## Format `.meta.json`

```json
{
  "url": "https://thuvienphapluat.vn/van-ban/...",
  "title": "Luật Giao thông đường bộ 2008",
  "document_number": "23/2008/QH12",
  "issued_date": "2008-11-13",
  "effective_date": "2009-07-01",
  "domain": "giao_thong"
}
```

## Format processed JSONL

Xem `docs/data-model.md`.
