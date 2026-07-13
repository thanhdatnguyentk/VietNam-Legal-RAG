"""End-to-End RAG Evaluator using LLM-as-a-Judge."""

import json
from pathlib import Path
from tqdm import tqdm
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from vietnam_legal_rag.pipeline.rag import RAGPipeline
from vietnam_legal_rag.config import get_settings

class EvaluationScore(BaseModel):
    faithfulness: int = Field(description="1 nếu câu trả lời hoàn toàn dựa trên context, 0 nếu bịa đặt (hallucination) hoặc lấy thông tin ngoài context.")
    relevance: int = Field(description="1 nếu câu trả lời giải quyết trực tiếp câu hỏi, 0 nếu trả lời lạc đề hoặc không đầy đủ.")
    reasoning: str = Field(description="Giải thích ngắn gọn cho số điểm trên.")

class E2EEvaluator:
    def __init__(self, pipeline: RAGPipeline, testset_path: Path):
        self.pipeline = pipeline
        self.testset_path = testset_path
        
        self.judge_llm = ChatOllama(
            model="qwen2.5:1.5b",
            temperature=0,
            base_url="http://localhost:11434"
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Bạn là một chuyên gia đánh giá hệ thống RAG (Retrieval-Augmented Generation) trong lĩnh vực pháp luật Việt Nam.
Nhiệm vụ của bạn là đánh giá tính trung thực (Faithfulness) và tính liên quan (Relevance) của Câu trả lời so với Câu hỏi và Ngữ cảnh được cung cấp.

- Faithfulness: Câu trả lời có được suy ra hoàn toàn từ Ngữ cảnh không? (1 nếu hoàn toàn dựa trên context, 0 nếu bịa đặt hoặc lấy thông tin ngoài).
- Relevance: Câu trả lời có trả lời đúng trọng tâm Câu hỏi không? (1 nếu đúng trọng tâm, 0 nếu lạc đề).

Bạn PHẢI trả về ĐÚNG một chuỗi JSON hợp lệ với định dạng sau (và KHÔNG THÊM BẤT KỲ VĂN BẢN NÀO KHÁC):
{{
  "faithfulness": 1 hoặc 0,
  "relevance": 1 hoặc 0,
  "reasoning": "Giải thích ngắn gọn"
}}"""),
            ("user", """
CÂU HỎI: {question}

NGỮ CẢNH ĐƯỢC CUNG CẤP (RETRIEVED CONTEXT):
{context}

CÂU TRẢ LỜI CỦA HỆ THỐNG:
{answer}
""")
        ])
        
        self.eval_chain = self.prompt | self.judge_llm

    def run(self, max_samples: int = 50) -> dict:
        if not self.testset_path.exists():
            raise FileNotFoundError(f"Testset not found: {self.testset_path}")

        total_faithfulness = 0
        total_relevance = 0
        total_samples = 0
        
        results = []

        with open(self.testset_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for line in tqdm(lines[:max_samples], desc="Evaluating E2E"):
            if not line.strip(): continue
            record = json.loads(line)
            question = record["question"]
            
            # Run the RAG pipeline
            rag_answer = self.pipeline.query(question)
            answer_text = rag_answer.answer
            hits = rag_answer.hits
            
            # Reconstruct context text
            context_text = "\n\n".join([f"[{i+1}] {hit.document.page_content}" for i, hit in enumerate(hits)])
            
            try:
                response = self.eval_chain.invoke({
                    "question": question,
                    "context": context_text,
                    "answer": answer_text
                })
                
                # Try to parse JSON from the text
                output_text = response.content.strip()
                if output_text.startswith("```json"):
                    output_text = output_text[7:]
                if output_text.endswith("```"):
                    output_text = output_text[:-3]
                    
                score = json.loads(output_text.strip())
                
                total_faithfulness += score.get("faithfulness", 0)
                total_relevance += score.get("relevance", 0)
                total_samples += 1
                
                results.append({
                    "question": question,
                    "answer": answer_text,
                    "faithfulness": score.get("faithfulness", 0),
                    "relevance": score.get("relevance", 0),
                    "reasoning": score.get("reasoning", "")
                })
            except Exception as e:
                print(f"Error evaluating question '{question}': {e}")
                continue

        return {
            "faithfulness_score": total_faithfulness / total_samples if total_samples > 0 else 0,
            "relevance_score": total_relevance / total_samples if total_samples > 0 else 0,
            "total_samples": total_samples,
            "details": results
        }
