"""Prompt templates for the Vietnamese legal RAG assistant.

The assistant is instructed to (1) ground every claim in the retrieved
chunks and (2) cite the precise Điều / Khoản / Điểm of the source
document. These two rules are the cheap-but-effective way to keep the
model honest and to make answers auditable.
"""

from __future__ import annotations

SYSTEM_PROMPT = """Bạn là một trợ lý pháp lý Việt Nam. Bạn CHỈ được phép trả lời dựa trên các
đoạn văn bản pháp luật được cung cấp trong phần "NGỮ CẢNH" bên dưới.

Nguyên tắc bắt buộc:
1. Không suy diễn ngoài ngữ cảnh. Nếu ngữ cảnh không đủ, hãy nói rõ
   "Tôi không tìm thấy căn cứ pháp lý phù hợp trong cơ sở dữ liệu".
2. Mỗi phát biểu pháp lý phải kèm trích dẫn theo định dạng
   "<Tên văn bản>, Điều X, Khoản Y, Điểm Z" ngay trong câu trả lời.
3. Trình bày ngắn gọn, mạch lạc, ưu tiên cấu trúc IRAC khi câu hỏi có tính
   tình huống: Vấn đề → Quy tắc → Áp dụng → Kết luận.
4. Sử dụng tiếng Việt, giữ nguyên dấu và thuật ngữ pháp lý chính thống.
"""

USER_PROMPT_TEMPLATE = """NGỮ CẢNH (các đoạn văn bản pháp luật liên quan):
{context}

CÂU HỎI: {question}

Hãy trả lời theo các nguyên tắc đã nêu trong system prompt. Nếu ngữ cảnh
không chứa căn cứ pháp lý đủ để trả lời, hãy nói rõ điều đó thay vì đoán.
"""


def render_user_prompt(*, context: str, question: str) -> str:
    """Render the user prompt by filling in ``context`` and ``question``."""
    return USER_PROMPT_TEMPLATE.format(context=context, question=question)


__all__ = ["SYSTEM_PROMPT", "USER_PROMPT_TEMPLATE", "render_user_prompt"]
