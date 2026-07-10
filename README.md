# ⚖️ VietLegal RAG - Trợ Lý Pháp Luật AI Tối Thượng

Hệ thống RAG (Retrieval-Augmented Generation) tiên tiến chuyên biệt cho lĩnh vực pháp luật Việt Nam. Được thiết kế để giải quyết các thách thức đặc thù của văn bản luật: truy hồi cấu trúc thứ bậc, tham chiếu chéo (Graph RAG), và lập luận pháp lý chính xác (IRAC).

![VietLegal RAG Architecture](docs/ARCHITECTURE.md) *(Placeholder for architecture image if any)*

---

## 🌟 Điểm Nổi Bật

*   **Hybrid Retrieval + Cross-Encoder Reranker**: Kết hợp `BGE-M3` (Dense) và `BM25` (Sparse) qua Reciprocal Rank Fusion, sau đó rerank bằng `bge-reranker-v2-m3` để đạt độ chính xác truy hồi **74.00% Recall@5**.
*   **Knowledge Graph RAG (Neo4j)**: Tự động trích xuất các mối quan hệ `Sửa đổi`, `Bổ sung`, `Thay thế` giữa các văn bản để cung cấp bối cảnh đầy đủ cho LLM, tránh lỗi trích dẫn luật hết hiệu lực.
*   **Hierarchical Chunking**: Kỹ thuật phân mảnh văn bản thông minh theo cấu trúc `Phần → Chương → Mục → Điều → Khoản → Điểm` đặc thù của Luật Việt Nam.
*   **Prompting IRAC CoT**: Ép buộc LLM lập luận theo chuẩn pháp lý: `Issue (Vấn đề)` → `Rule (Quy định)` → `Application (Áp dụng)` → `Conclusion (Kết luận)`.
*   **Giao Diện UI/UX Pro Max**: Giao diện chuẩn Material Design 3 (Google Gemini style) với Dark Mode, Glassmorphism và streaming responses.

---

## 🚀 Hướng Dẫn Nhanh (Quick Start)

### 1. Yêu cầu hệ thống
*   Python 3.12+
*   Docker & Docker Compose (cho Neo4j, Redis, Nginx)
*   NVIDIA GPU (khuyến nghị cho Embedding và Reranker)
*   API Keys (OpenAI, Gemini hoặc Anthropic)

### 2. Cài đặt

Clone repository và cài đặt môi trường:
```bash
git clone https://github.com/your-username/VietLegalRag.git
cd VietLegalRag

# Khởi tạo môi trường ảo (ví dụ: dùng venv hoặc conda)
python -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies (sử dụng pip hoặc uv)
pip install -r pyproject.toml # Hoặc uv sync
```

### 3. Cấu hình

Tạo file `.env` từ `.env.example`:
```bash
cp .env.example .env
```
Điền các API key của bạn vào `.env` (ví dụ: `GEMINI_API_KEY`, `OPENAI_API_KEY`).

### 4. Khởi chạy toàn bộ hệ thống (Production Mode)

Hệ thống cung cấp sẵn `docker-compose.yml` chứa FastAPI, Neo4j, và Frontend Nginx.

```bash
docker-compose up -d --build
```

Sau khi khởi chạy:
*   **Giao diện Chat**: `http://localhost:80`
*   **API Server**: `http://localhost:8000/docs`
*   **Neo4j Browser**: `http://localhost:7474` (Tài khoản: `neo4j` / Mật khẩu: `VietLegal123`)

---

## 🛠️ Công Cụ Dòng Lệnh (CLI)

Nếu bạn muốn chạy các thành phần riêng lẻ hoặc thử nghiệm (không dùng Docker), dự án cung cấp bộ CLI rất mạnh qua `scripts/`:

### Data Ingestion (Import dữ liệu)
```bash
# Tiền xử lý, cắt chunk, và tạo embedding vector đưa vào ChromaDB
PYTHONPATH=src python scripts/ingest.py ./data/raw/
```

### Knowledge Graph Builder (Xây dựng Graph)
```bash
# Trích xuất quan hệ từ các chunk và đưa vào Neo4j
PYTHONPATH=src python scripts/build_graph.py
```

### Chạy truy vấn RAG qua Terminal
```bash
# Hỏi AI với thuật toán Hybrid + Reranker + Graph
PYTHONPATH=src python scripts/query.py --query "Mức phạt vượt đèn đỏ xe máy?" --hybrid --rag
```

### Đánh giá (Evaluation)
```bash
# Chạy đánh giá Ablation Study đo đạc các thuật toán Retrieval
PYTHONPATH=src python scripts/ablation.py
```

---

## 📚 Tài Liệu Kỹ Thuật

*   [Kế hoạch & Báo cáo triển khai chi tiết](docs/IMPLEMENTATION_PLAN.md)
*   [API Documentation (Swagger) - Sau khi chạy server](http://localhost:8000/docs)

---

## 👨‍💻 Tác giả
Phát triển bởi đội ngũ đam mê ứng dụng AI vào Pháp luật Việt Nam.
