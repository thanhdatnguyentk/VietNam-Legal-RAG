import json
import random
from pathlib import Path

def generate_question(chunk):
    meta = chunk["metadata"]
    doc_num = meta["document_number"]
    article = meta.get("article", "")
    article_title = meta.get("article_title", "")
    domain = meta.get("domain", "")

    # Clean up the article title a bit
    article_title = article_title.strip(".,;: ")
    
    if not article or not article_title:
        return None

    templates = [
        f"Theo văn bản {doc_num}, quy định về {article_title.lower()} được nêu ở đâu và như thế nào?",
        f"Nội dung quy định tại Điều {article} của {doc_num} là gì?",
        f"Văn bản {doc_num} quy định thế nào về việc: {article_title.lower()}?",
        f"Chi tiết Điều {article} trong {doc_num} về {article_title.lower()}?",
        f"Trong lĩnh vực {domain}, {doc_num} hướng dẫn về {article_title.lower()} ra sao?"
    ]
    return random.choice(templates)

def main():
    processed_dir = Path("data/processed")
    all_chunks = []
    
    for jsonl_file in processed_dir.rglob("*.jsonl"):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                chunk = json.loads(line)
                meta = chunk["metadata"]
                if meta.get("article") and len(meta.get("article_title", "")) > 10:
                    all_chunks.append(chunk)
                    
    # Lấy mẫu 200 chunks (hoặc nhiều hơn)
    sample_size = min(200, len(all_chunks))
    sampled_chunks = random.sample(all_chunks, sample_size)

    results = []
    for chunk in sampled_chunks:
        q = generate_question(chunk)
        if q:
            results.append({
                "question": q,
                "ground_truth_document_number": chunk["metadata"]["document_number"],
                "ground_truth_chunk_id": chunk["metadata"].get("chunk_id", ""),
            })

    output_path = Path("data/eval/questions.v2.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"Done! Generated {len(results)} rule-based questions at {output_path}")

if __name__ == "__main__":
    main()
