import json
import random
import torch
from pathlib import Path
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

def main():
    print("Loading local model (Qwen2.5-1.5B-Instruct)...")
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    processed_dir = Path("data/processed")
    all_chunks = []
    print("Reading JSONL files...")
    for jsonl_file in processed_dir.rglob("*.jsonl"):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                chunk = json.loads(line)
                if len(chunk["text"]) > 150: # Only use decent sized chunks
                    all_chunks.append(chunk)

    print(f"Total chunks found: {len(all_chunks)}")
    
    sample_size = min(200, len(all_chunks))
    sampled_chunks = random.sample(all_chunks, sample_size)

    results = []
    print(f"Generating {sample_size} questions using local GPU...")
    
    for chunk in tqdm(sampled_chunks):
        text = chunk["text"]
        prompt = f"""Bạn là một chuyên gia pháp lý. Dựa vào nội dung văn bản dưới đây, hãy tạo ra duy nhất MỘT câu hỏi pháp lý thực tế mà người dân có thể hỏi.
ĐÁP ÁN CỦA CÂU HỎI PHẢI NẰM TRONG ĐOẠN VĂN BẢN NÀY. KHÔNG thêm lời giải thích.

Văn bản:
{text[:1000]}

Câu hỏi:"""
        
        messages = [
            {"role": "system", "content": "Bạn là trợ lý ảo chuyên tạo câu hỏi trắc nghiệm/pháp lý ngắn gọn."},
            {"role": "user", "content": prompt}
        ]
        
        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text_input], return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
        generated_ids = outputs[0][len(inputs.input_ids[0]):]
        question = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        
        # Clean up output if model is overly chatty
        if "Câu hỏi:" in question:
            question = question.split("Câu hỏi:")[-1].strip()
            
        results.append({
            "question": question,
            "ground_truth_document_number": chunk["metadata"]["document_number"],
            "ground_truth_chunk_id": chunk["metadata"].get("chunk_id", ""),
        })

    output_path = Path("data/eval/questions.v2.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"\nDone! Generated {len(results)} questions at {output_path}")

if __name__ == "__main__":
    main()
