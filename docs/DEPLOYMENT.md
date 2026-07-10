# Hướng Dẫn Triển Khai (Deployment Guide)

VietLegal RAG được đóng gói hoàn toàn bằng Docker Compose để đảm bảo tính nhất quán giữa các môi trường từ Development đến Production.

## Cấu Trúc Cluster

Hệ thống bao gồm 3 services chính:
1.  **`neo4j`**: Lưu trữ Knowledge Graph, mapping cổng `7474` (web UI) và `7687` (Bolt).
2.  **`api`**: FastAPI Backend. Khởi chạy bằng Uvicorn, mapping cổng `8000`. Cần GPU passthrough để tối ưu tốc độ Embedding/Reranking.
3.  **`frontend`**: Nginx Alpine, phục vụ file tĩnh giao diện Material Design 3 tại cổng `80`.

## 1. Yêu Cầu Máy Chủ (Production)
*   **CPU**: 4-8 Cores (để chạy LLM clients/BM25)
*   **RAM**: Khuyến nghị 16GB (để chứa BM25 Index in-memory & Neo4j caching).
*   **GPU**: NVIDIA (T4 / L4 / RTX 3060+) có cài đặt `nvidia-container-toolkit` để chạy Docker với GPU.

## 2. Các Bước Triển Khai

```bash
# 1. Kéo mã nguồn
git clone https://github.com/your-username/VietLegalRag.git
cd VietLegalRag

# 2. Tạo biến môi trường
cp .env.example .env
nano .env # (Cấu hình GEMINI_API_KEY, NEO4J_URI=bolt://neo4j:7687, v.v.)

# 3. Build & Run
docker-compose up -d --build
```

## 3. Cập nhật Dữ Liệu
Để update ChromaDB hoặc Neo4j, bạn có thể exec vào container API:
```bash
docker-compose exec api bash
python scripts/ingest.py ./data/raw/
python scripts/build_graph.py
```

## 4. Troubleshooting
*   **Lỗi không thấy GPU**: Kiểm tra `nvidia-smi` và đảm bảo trong file `docker-compose.yml` service `api` có cấu hình `deploy: resources: reservations: devices`.
*   **Neo4j không kết nối**: Do API startup nhanh hơn Neo4j, API có cơ chế auto-retry. Nếu vẫn lỗi, kiểm tra credentials trong `.env` và `docker-compose.yml` (`NEO4J_AUTH`).
