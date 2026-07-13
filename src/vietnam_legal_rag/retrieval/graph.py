"""Graph-enhanced Retriever using Neo4j Knowledge Graph."""

import logging
from typing import Any, List, Optional

from langchain_core.documents import Document

from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.graph.neo4j_client import Neo4jClient
from vietnam_legal_rag.graph.queries import GraphQuerier

logger = logging.getLogger(__name__)

class GraphEnhancedRetriever:
    """Enhances base retriever hits with multi-hop Knowledge Graph contexts."""

    def __init__(self, base_retriever: Any, neo4j_client: Neo4jClient):
        self.base_retriever = base_retriever
        self.client = neo4j_client
        self.querier = GraphQuerier(neo4j_client)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
        **kwargs: Any,
    ) -> List[RetrievalHit]:
        """Retrieve hits using base retriever and expand via KG."""
        # 1. Get base hits (Dense + BM25 + Rerank)
        base_hits = self.base_retriever.retrieve(query, top_k=top_k, domain=domain, **kwargs)
        
        # 2. Extract context from Graph
        expanded_hits = list(base_hits)
        seen_docs = {hit.document.metadata.get("document_number") for hit in base_hits if hit.document.metadata.get("document_number")}
        
        # Expand based on top 3 hits to save time
        for hit in base_hits[:3]:
            doc_number = hit.document.metadata.get("document_number")
            if not doc_number:
                continue
                
            # Query graph for amendments
            try:
                amendments = self.querier.get_document_amendments(doc_number)
                for amend in amendments:
                    # E.g., {'amending_article': 'doc1_art_2', 'content': '...'}
                    content = amend.get("content")
                    if content:
                        doc = Document(
                            page_content=f"[Graph Expansion - Sửa đổi/Bổ sung cho {doc_number}]\n" + content,
                            metadata={"source": "Knowledge Graph", "document_number": doc_number, "type": "amendment"}
                        )
                        # Add as a new hit with slightly lower score
                        new_hit = RetrievalHit(
                            document=doc,
                            score=hit.score * 0.9, # slightly penalize expanded context
                            rank=len(expanded_hits) + 1
                        )
                        expanded_hits.append(new_hit)
            except Exception as e:
                logger.warning(f"Graph expansion failed for {doc_number}: {e}")
                
        # Re-sort just in case, and deduplicate (simplified)
        expanded_hits.sort(key=lambda x: x.score, reverse=True)
        
        # Re-assign ranks
        for i, hit in enumerate(expanded_hits):
            hit.rank = i + 1
            
        return expanded_hits

