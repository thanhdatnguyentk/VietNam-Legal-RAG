"""Test script for Graph-Enhanced RAG."""

import logging
from langchain_core.documents import Document

from vietnam_legal_rag.graph.neo4j_client import Neo4jClient
from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.retrieval.graph import GraphEnhancedRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DummyRetriever:
    """Mock base retriever that returns a single document."""
    def retrieve(self, query: str, k: int = 5, **kwargs) -> list[RetrievalHit]:
        doc = Document(
            page_content="Luật số 100/2019/QH14 về Giao thông đường bộ quy định...",
            metadata={"document_number": "100/2019/QH14"}
        )
        return [RetrievalHit(document=doc, score=0.9, rank=1)]

def setup_mock_graph(client: Neo4jClient):
    """Insert a mock document and a mock amendment into Neo4j."""
    logger.info("Setting up mock graph relations...")
    
    # 1. Insert Base Document
    client.execute_query('''
        MERGE (d:LegalDocument {id: "doc_100_2019"})
        SET d.number = "100/2019/QH14", d.title = "Luật Giao thông"
    ''')
    
    # 2. Insert Amending Article
    client.execute_query('''
        MERGE (a:Article {id: "art_suy_doi_1"})
        SET a.content = "Nghị định này sửa đổi, bổ sung Điều 5 của Luật số 100/2019/QH14",
            a.number = "Điều 1"
        
        WITH a
        MATCH (d:LegalDocument {number: "100/2019/QH14"})
        MERGE (a)-[:AMENDS]->(d)
    ''')
    logger.info("Mock graph setup complete.")

if __name__ == "__main__":
    with Neo4jClient() as client:
        # 1. Setup mock data
        setup_mock_graph(client)
        
        # 2. Initialize retriever
        base = DummyRetriever()
        graph_retriever = GraphEnhancedRetriever(base_retriever=base, neo4j_client=client)
        
        # 3. Test Retrieval
        logger.info("Running retrieval for query: 'giao thông'")
        hits = graph_retriever.retrieve("giao thông")
        
        print("\n--- RETRIEVAL RESULTS ---")
        for i, hit in enumerate(hits):
            print(f"\nHit {i+1} (Score: {hit.score:.4f}):")
            print(f"Content: {hit.document.page_content}")
            print(f"Metadata: {hit.document.metadata}")
