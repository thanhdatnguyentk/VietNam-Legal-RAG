"""Custom citation accuracy checker for LLM evaluation."""

import re
from typing import List, Dict, Any

class CitationChecker:
    """Evaluates if the LLM successfully and accurately cites the correct legal documents."""
    
    def __init__(self):
        # Basic patterns to find citations like "[Luật Giao thông đường bộ 2008]" or "Điều 5, Nghị định 100/2019/NĐ-CP"
        self.doc_num_pattern = re.compile(r'([A-Za-z0-9]+/[0-9]{4}/[A-Za-z0-9ĐĐ-]+)')

    def extract_citations(self, text: str) -> List[str]:
        """Extract all legal document numbers from text."""
        return self.doc_num_pattern.findall(text)

    def evaluate(self, answer: str, ground_truth_doc_num: str) -> Dict[str, Any]:
        """
        Evaluate a single answer against its ground truth.
        Returns:
            - is_cited: whether ANY document was cited
            - is_correct_citation: whether the GROUND TRUTH document was cited
            - extracted_citations: list of found citations
        """
        citations = self.extract_citations(answer)
        is_cited = len(citations) > 0
        
        is_correct = False
        if ground_truth_doc_num:
            # Normalize for matching
            gt_norm = ground_truth_doc_num.strip().lower()
            for cit in citations:
                if gt_norm in cit.lower():
                    is_correct = True
                    break
                    
        return {
            "is_cited": is_cited,
            "is_correct_citation": is_correct,
            "extracted_citations": citations,
            "ground_truth": ground_truth_doc_num
        }

    def run_batch(self, dataset: List[Dict[str, str]]) -> Dict[str, float]:
        """Run evaluation on a dataset of {'answer': ..., 'ground_truth': ...}"""
        total = len(dataset)
        if total == 0:
            return {"citation_rate": 0.0, "citation_accuracy": 0.0}
            
        cited_count = 0
        correct_count = 0
        
        for item in dataset:
            res = self.evaluate(item["answer"], item["ground_truth"])
            if res["is_cited"]: cited_count += 1
            if res["is_correct_citation"]: correct_count += 1
            
        return {
            "citation_rate": cited_count / total,
            "citation_accuracy": correct_count / total
        }

if __name__ == "__main__":
    # Quick test
    checker = CitationChecker()
    ans = "Theo quy định tại Khoản 1 Điều 5 Nghị định 100/2019/NĐ-CP, hành vi này bị phạt 2 triệu đồng."
    print("Test extraction:", checker.evaluate(ans, "100/2019/NĐ-CP"))
