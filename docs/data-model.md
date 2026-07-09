# Data model

## 1. RawDocument (in-memory, trước khi ghi đĩa)

Trong `vietnam_legal_rag.scrapers.base.RawDocument`:

| Trường            | Kiểu            | Bắt buộc | Mô tả                                        |
|-------------------|-----------------|----------|----------------------------------------------|
| `url`             | `str`           | ✓        | URL nguồn gốc                                |
| `title`           | `str`           | ✓        | Tiêu đề văn bản                              |
| `document_number` | `str \| None`   |          | Số hiệu (vd. `"100/2019/NĐ-CP"`)            |
| `issued_date`     | `str \| None`   |          | ISO 8601 ngày ban hành                       |
| `effective_date`  | `str \| None`   |          | ISO 8601 ngày có hiệu lực                    |
| `domain`          | `str \| None`   |          | Khớp với `DomainSpec.name`                   |
| `body_text`       | `str`           | ✓        | Nội dung toàn văn                             |
| `extra_metadata`  | `dict[str,str]` |          | Bất kỳ thông tin phụ (người ký, loại văn bản) |

## 2. Raw file on disk

Mỗi văn bản được lưu thành **một cặp file**:

```
data/raw/<domain>/<số_hiệu>.txt
data/raw/<domain>/<số_hiệu>.meta.json
```

`<số_hiệu>.txt` chứa `body_text` thuần (UTF-8). `<số_hiệu>.meta.json` chứa các
trường metadata (trừ `body_text`) để loader có thể khôi phục `Document.metadata`.

## 3. Processed chunk (in-memory + JSONL)

Một chunk là một `langchain_core.documents.Document` với:

- `page_content`: văn bản đã được tách (theo Điều/Khoản/Điểm). **Bắt đầu bằng header
  citation** do chunker render — vd `23/2008/QH12 | Điều 5 — Quy định về nhiều khoản\n\nKhoản 1\n...`.
- `metadata` (dict): các trường sau là **bắt buộc** để citation chính xác:

| Khoá                | Kiểu    | Bắt buộc | Mô tả                                        |
|---------------------|---------|----------|----------------------------------------------|
| `document_number`   | `str`   | ✓        | Số hiệu văn bản                              |
| `document_title`    | `str`   | ✓        | Tên văn bản                                  |
| `domain`            | `str`   | ✓        | Tên miền                                     |
| `article`           | `str`   | ✓        | Số Điều (vd. `"15"`)                         |
| `article_title`     | `str`   |          | Tên Điều                                     |
| `clause`            | `str`   |          | Số Khoản (chuỗi rỗng khi split theo Điều)    |
| `point`             | `str`   |          | Chữ cái Điểm (chuỗi rỗng khi không có Điểm) |
| `chunk_id`          | `str`   | ✓        | UUID4 hex — **không ổn định giữa các run**   |
| `source_url`        | `str`   | ✓        | URL gốc                                      |

**Metadata bổ sung** (do chunker tính toán, không bắt buộc nhưng rất hữu ích):

| Khoá                | Kiểu    | Mô tả                                                          |
|---------------------|---------|----------------------------------------------------------------|
| `split_level`       | `str`   | `"article"` \| `"clause"` \| `"point"` \| `"char"` (fallback)   |
| `chunk_index`       | `int`   | Vị trí chunk trong document, 0-based                           |
| `total_chunks`      | `int`   | Tổng số chunk của document                                     |
| `url` / `title`     | `str`   | Alias của `source_url` / `document_title` từ sidecar (giữ lại để debug) |
| `issued_date`       | `str`   | ISO 8601 — chỉ có nếu sidecar có                               |
| `effective_date`    | `str`   | ISO 8601 — chỉ có nếu sidecar có                               |

> **Lưu ý quan trọng về `chunk_id`**: hiện tại là `uuid4().hex` — không ổn định giữa
> các lần chạy ingestion. Phase 3 (Vector store) sẽ cần chiến lược idempotency; nếu
> muốn `chunk_id` ổn định, dùng hash(document_number + article + clause + point + text_hash).
> Đây là trade-off đã chốt ở phase 2.

JSONL output mỗi dòng:

```json
{"text": "...", "metadata": {"document_number": "100/2019/NĐ-CP", "article": "15", ...}}
```

## 4. Vector store record (ChromaDB)

Mỗi vector trong ChromaDB tương ứng một chunk, với:

- `id`: trùng với `chunk_id`.
- `embedding`: vector float (chiều tuỳ model, vd. 768 cho SBERT).
- `document`: `chunk.text`.
- `metadata`: cùng schema với `Document.metadata` ở mục 3.

## 5. RetrievalHit

Trong `vietnam_legal_rag.retrieval.base.RetrievalHit`:

| Trường      | Kiểu       | Mô tả                                  |
|-------------|------------|----------------------------------------|
| `document`  | `Document` | Chunk được retrieve                     |
| `score`     | `float`    | Điểm cosine (cao = liên quan hơn)       |
| `rank`      | `int`      | Thứ hạng 1-based trong top-k           |

## 6. RAGAnswer

Trong `vietnam_legal_rag.pipeline.rag.RAGAnswer`:

| Trường        | Kiểu                | Mô tả                                |
|---------------|---------------------|--------------------------------------|
| `question`    | `str`               | Câu hỏi gốc                          |
| `answer`      | `str`               | Câu trả lời từ LLM                   |
| `citations`   | `list[str]`         | Chuỗi citation đã parse từ answer    |
| `hits`        | `Sequence[RetrievalHit]` | Các chunk đã dùng để sinh answer |

## 7. EvalReport

Trong `vietnam_legal_rag.eval.evaluator.EvalReport`:

| Trườnng                       | Kiểu     | Mô tả                                |
|-------------------------------|----------|--------------------------------------|
| `total`                       | `int`    | Số câu hỏi trong eval set            |
| `retrieval_precision_at_k`    | `float`  | Precision @ k                        |
| `retrieval_recall_at_k`       | `float`  | Recall @ k                           |
| `answer_faithfulness`         | `float?` | Điểm faithfulness (nếu có judge)     |
