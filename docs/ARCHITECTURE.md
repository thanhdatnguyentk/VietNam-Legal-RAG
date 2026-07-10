# Kiến Trúc Hệ Thống VietLegal RAG

Hệ thống được thiết kế theo hướng module, phân tách rõ ràng giữa Pipeline Xử Lý Dữ Liệu (Offline) và Pipeline Phục Vụ Truy Vấn (Online).

## 1. Data Ingestion Pipeline (Offline)

Đóng vai trò nền tảng để cung cấp tri thức cho hệ thống:
1.  **Raw Data**: Dữ liệu dạng JSON từ `thuvienphapluat.vn` (chứa các metadata như ngày ban hành, cơ quan ban hành).
2.  **Chunker (`StructuralVietnameseChunker`)**: Sử dụng Regex Parsing cực kỳ phức tạp để bắt các node: Phần → Chương → Mục → Điều → Khoản → Điểm. Kèm theo cơ chế *Title Enrichment* (Gắn bối cảnh cấu trúc vào text của chunk).
3.  **Vectorization**: Dùng model `BAAI/bge-m3` chuyển đổi nội dung tiếng Việt sang không gian vector 1024 chiều, đẩy vào ChromaDB.
4.  **Graph Extraction**: Duyệt qua nội dung, trích xuất số hiệu văn bản gốc và dùng regex bắt các từ khóa ("sửa đổi", "bổ sung Điều... của Luật số..."). Đẩy Entity và Relation vào Neo4j.

## 2. Retrieval & RAG Pipeline (Online)

Khi User đặt câu hỏi, luồng xử lý diễn ra trong khoảng ~2 giây:

1.  **Query Parsing**: FastAPI nhận câu hỏi từ UI.
2.  **Hybrid Retrieval**: 
    *   Truy vấn đồng thời vào BM25 (chuyên bắt keyword số hiệu) và ChromaDB (chuyên bắt ngữ nghĩa).
    *   Hòa trộn kết quả bằng thuật toán RRF (Reciprocal Rank Fusion).
3.  **Cross-Encoder Reranking**: Đẩy top 50 kết quả từ RRF qua model `bge-reranker-v2-m3` để chấm điểm lại sự liên quan giữa câu hỏi và từng chunk. Lấy Top 5 kết quả tốt nhất.
4.  **Knowledge Graph Expansion**: (Tính năng độc quyền)
    *   Với Top 5 chunk vừa tìm được, tìm số hiệu văn bản của chúng.
    *   Truy vấn Neo4j lấy toàn bộ các văn bản đang *sửa đổi* hoặc *bổ sung* cho chúng. Gắn thêm vào context.
5.  **LLM Generation**: Sử dụng Prompt theo chuẩn IRAC (Issue - Rule - Application - Conclusion) gửi context tới Gemini/OpenAI để sinh ra câu trả lời cuối cùng, kèm theo trích dẫn chính xác.
