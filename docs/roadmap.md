# Roadmap

Repo hiện ở giai đoạn **Skeleton + tài liệu** (v0.1.0-alpha). Các phase tiếp theo
được ưu tiên như sau.

## Phase 2 — Ingestion thật (ưu tiên cao) ✅ DONE

**Mục tiêu**: từ 1 văn bản luật thô → file JSONL chunks chất lượng cao.

- [x] Implement `TxtDocumentLoader.load()` (đọc `.txt` + `.meta.json`, map `title` → `document_title`, `url` → `source_url`, fallback domain từ tên thư mục hoặc `"unknown"`).
- [x] Implement `RecursiveVietnameseChunker.split()` — splitter 3 cấp (Điều → Khoản → Điểm) với `langchain-text-splitters` làm fallback cho phần quá dài.
- [x] Thêm unit test: 22 tests mới (regex, loader, chunker, pipeline end-to-end), 36 tests tổng cộng đều pass.
- [x] Thêm `src/vietnam_legal_rag/ingestion/_regex.py` với các compiled regex (hỗ trợ cả chữ Việt `đ`).
- [x] Thêm fixture `tests/fixtures/sample_law.{txt,meta.json}` mô phỏng Luật Giao thông đường bộ 2008.
- [x] Update `scripts/ingest.py` với `--dry-run --stats -v`.
- [x] Update `docs/data-model.md` với các metadata computed (`split_level`, `chunk_index`, `total_chunks`) và ghi chú về `chunk_id` không ổn định giữa các run.

**Decisions đã chốt ở phase 2**:
- Chunk_id = `uuid4().hex` (không ổn định; idempotency cho phase 3 dùng hash).
- Nếu Khoản > chunk_size mà không có Điểm: emit 1 oversized chunk thay vì char-split (giữ semantic boundary).
- Test file thật chưa commit — đợi user cung cấp sau (do robots.txt của TVPL cấm `ai-input`).

## Phase 3 — Embedding + Index

- [ ] Implement `VietnameseEmbedder._load()` (lazy load `sentence_transformers`).
- [ ] Implement `VectorStore._connect()`, `add()`, `query()` trên ChromaDB.
- [ ] Implement `build_index.py` (đọc JSONL → embed → upsert).
- [ ] Smoke test: truy vấn 5 câu thủ công, xem top-5 hits có hợp lý không.

## Phase 4 — Generation

- [ ] Implement `build_default_llm()` (OpenAI + Anthropic branches).
- [ ] Implement `RAGPipeline.query()`:
      1. retrieve top-k
      2. build context với header (Điều/Khoản)
      3. gọi LLM với system + user prompt
      4. parse citations từ answer
- [ ] Test end-to-end với 5-10 câu hỏi mẫu.
- [ ] Thêm chế độ `--interactive` REPL vào `scripts/query.py` (đã có skeleton).

## Phase 5 — Evaluation

- [ ] Tạo `data/eval/questions.v1.jsonl` ≥ 30 câu, có ground-truth:
      `{id, question, expected_articles, expected_answer}`.
- [ ] Implement `Evaluator`:
      - Retrieval precision@k, recall@k
      - Answer faithfulness (LLM-as-judge hoặc rule-based overlap)
- [ ] Tạo `scripts/eval.py` (đã có skeleton).
- [ ] Baseline số trên bộ eval, lưu vào `docs/eval-baseline.md`.

## Phase 6 — Polish & multi-agent (tùy chọn)

- [ ] FastAPI wrapper quanh `RAGPipeline` (`POST /query`).
- [ ] Web UI (Streamlit hoặc Gradio) cho demo.
- [ ] **Hybrid retrieval** (BM25 + dense, λ=0.7).
- [ ] **Cross-encoder reranker** (BGE-reranker-v2-m3).
- [ ] **Router Agent** + **Specialized Agents** (Statutory / Case Law / Compliance).
- [ ] **Legal Knowledge Graph** (Neo4j): node = Điều, edge = `Amends` / `Replaces` / `Refers_To`.
- [ ] CI workflow (lint + test + eval smoke).

## Đóng góp

Khi làm theo bất kỳ phase nào ở trên, hãy:

1. Tạo branch riêng (`phase-2-ingestion`, …).
2. Giữ các module skeleton làm **fallback** nếu cần (đừng xoá abstract base).
3. Thêm test tương ứng với mỗi implementation.
4. Cập nhật README/docs liên quan trong cùng PR.
