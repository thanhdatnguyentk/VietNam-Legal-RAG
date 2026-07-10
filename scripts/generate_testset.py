"""Generate synthetic evaluation dataset."""
import json
import random
import asyncio
from pathlib import Path
from tqdm.asyncio import tqdm
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from vietnam_legal_rag.config import get_settings

PROMPT = PromptTemplate.from_template(
    """Bạn là một chuyên gia pháp lý. Dựa vào nội dung văn bản dưới đây, hãy tạo ra MỘT câu hỏi pháp lý thực tế mà một người dân hoặc doanh nghiệp có thể hỏi.
Câu hỏi phải tự nhiên, mang tính thực tiễn, và ĐÁP ÁN CỦA CÂU HỎI PHẢI NẰM TRONG ĐOẠN VĂN BẢN NÀY.
KHÔNG sử dụng các cụm từ như "Theo văn bản này", "Đoạn văn này nói gì".
Chỉ trả về duy nhất nội dung câu hỏi, không thêm bất kỳ văn bản nào khác.

[NỘI DUNG VĂN BẢN]:
{text}
"""
)

async def generate_question(llm, chunk):
    text = chunk["text"]
    try:
        chain = PROMPT | llm
        response = await chain.ainvoke({"text": text})
        question = response.content.strip()
        return {
            "question": question,
            "ground_truth_document_number": chunk["metadata"]["document_number"],
            "ground_truth_chunk_id": chunk["metadata"].get("chunk_id", ""),
            "metadata": chunk["metadata"]
        }
    except Exception as e:
        return None

async def main():
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0.7,
        max_retries=3,
    )

    # 1. Thu thập tất cả các chunks
    processed_dir = Path("data/processed")
    all_chunks = []
    print("Reading all JSONL files...")
    for jsonl_file in processed_dir.rglob("*.jsonl"):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                chunk = json.loads(line)
                if len(chunk["text"]) > 100: # Lọc các chunk quá ngắn
                    all_chunks.append(chunk)

    print(f"Total chunks found: {len(all_chunks)}")
    
    # 2. Lấy mẫu ngẫu nhiên 200 chunks
    sample_size = min(200, len(all_chunks))
    sampled_chunks = random.sample(all_chunks, sample_size)

    # 3. Tạo câu hỏi song song (giới hạn concurrency để tránh rate limit)
    print(f"Generating {sample_size} questions using Gemini...")
    sem = asyncio.Semaphore(10) # 10 concurrent requests

    async def sem_task(chunk):
        async with sem:
            return await generate_question(llm, chunk)

    tasks = [sem_task(chunk) for chunk in sampled_chunks]
    
    results = []
    for f in tqdm.as_completed(tasks, total=len(tasks)):
        res = await f
        if res:
            results.append(res)

    # 4. Ghi ra file
    output_path = Path("data/eval/questions.v2.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"\nDone! Generated {len(results)} questions at {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
