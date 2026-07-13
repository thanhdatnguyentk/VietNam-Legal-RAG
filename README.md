# ⚖️ VietLegal RAG - Trợ Lý Pháp Luật AI Tối Thượng

Hệ thống RAG (Retrieval-Augmented Generation) tiên tiến chuyên biệt cho lĩnh vực pháp luật Việt Nam. Được thiết kế để giải quyết các thách thức đặc thù của văn bản luật: truy hồi cấu trúc thứ bậc, tham chiếu chéo (Graph RAG), và lập luận pháp lý chính xác (IRAC).

![VietLegal RAG Architecture](docs/ARCHITECTURE.md) *(Placeholder for architecture image if any)*

---

## 🌟 Điểm Nổi Bật

* **Local LLM (100% Offline)**: Tích hợp `Ollama` chạy trực tiếp bằng Local GPU (Card NVIDIA) với model `Qwen 2.5 (1.5B/7B)`, không cần phụ thuộc vào API bên ngoài (Gemini/OpenAI), giúp bảo mật dữ liệu tuyệt đối và không giới hạn Rate Limit.
* **Hybrid Retrieval + Cross-Encoder Reranker**: Kết hợp `BGE-M3` (Dense) và `BM25` (Sparse) qua Reciprocal Rank Fusion, sau đó rerank bằng `bge-reranker-v2-m3` để đạt độ chính xác truy hồi **74.00% Recall@5**.
* **Knowledge Graph RAG (Neo4j)**: Tự động trích xuất các mối quan hệ `Sửa đổi`, `Bổ sung`, `Thay thế` giữa các văn bản để cung cấp bối cảnh đầy đủ cho LLM, tránh lỗi trích dẫn luật hết hiệu lực.
* **Hierarchical Chunking**: Kỹ thuật phân mảnh văn bản thông minh theo cấu trúc `Phần → Chương → Mục → Điều → Khoản → Điểm` đặc thù của Luật Việt Nam.
* **Prompting IRAC CoT**: Ép buộc LLM lập luận theo chuẩn pháp lý: `Issue (Vấn đề)` → `Rule (Quy định)` → `Application (Áp dụng)` → `Conclusion (Kết luận)`.
* **Giao Diện UI/UX Pro Max**: Giao diện chuẩn Material Design 3 (Google Gemini style) với Dark Mode, Glassmorphism và streaming responses.

---

## 🚀 Hướng Dẫn Nhanh (Quick Start)

### 1. Yêu cầu hệ thống

* Python 3.12+
* Docker & Docker Compose (cho API, Ollama, Neo4j, Nginx)
* NVIDIA GPU (Bắt buộc dùng `NVIDIA Container Toolkit` để Inference mô hình LLM, Embedding, và Reranker)

### 2. Cấu hình

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Mặc định hệ thống sử dụng **Ollama** với model `qwen2.5:1.5b`. Đảm bảo trong `.env` có cấu hình:
```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:1.5b
```

### 3. Khởi chạy toàn bộ hệ thống (Production Mode)

Hệ thống cung cấp sẵn `docker-compose.yml` chứa FastAPI, Ollama (GPU-accelerated), Neo4j, và Frontend Nginx.

```bash
# Khởi chạy các container
docker-compose up -d --build

# Kéo model LLM về Ollama (Chạy lần đầu)
docker exec vietlegalrag-ollama-1 ollama run qwen2.5:1.5b
```

Sau khi khởi chạy:

* **Giao diện Chat**: `http://localhost:80` (hoặc `http://localhost`)
* **API Server**: `http://localhost:8000/docs`
* **Neo4j Browser**: `http://localhost:7474` (Tài khoản: `neo4j` / Mật khẩu: `VietLegal123`)

---

## 🛠️ Công Cụ Dòng Lệnh (CLI)

Nếu bạn muốn chạy các thành phần riêng lẻ hoặc thử nghiệm (không dùng Docker), dự án cung cấp bộ CLI rất mạnh qua `scripts/`:

### Data Ingestion (Import dữ liệu)

```bash
# Tiền xử lý, cắt chunk, và tạo embedding vector đưa vào ChromaDB
PYTHONPATH=src python scripts/ingest.py ./data/raw/
```

### Chạy truy vấn RAG qua Terminal

```bash
# Hỏi AI với thuật toán Hybrid + Reranker + Graph
PYTHONPATH=src python scripts/query.py --query "Mức phạt vượt đèn đỏ xe máy?" --hybrid --rag
```

### Đánh giá (End-to-End Evaluation)

```bash
# Đánh giá câu trả lời tạo ra từ Ollama/Qwen so với Gemini Judge
PYTHONPATH=src python scripts/eval_e2e.py
```

---

## 📚 Tài Liệu Kỹ Thuật

* [Kế hoạch & Báo cáo triển khai chi tiết](docs/IMPLEMENTATION_PLAN.md)
* [Hướng dẫn Triển khai Deployment](docs/DEPLOYMENT.md)

---

## 👨‍💻 Tác giả

Phát triển bởi đội ngũ đam mê ứng dụng AI vào Pháp luật Việt Nam.
