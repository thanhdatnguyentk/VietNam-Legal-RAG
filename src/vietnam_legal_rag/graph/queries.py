"""Multi-hop traversal queries for the Legal Knowledge Graph."""

import logging
from typing import List, Dict, Any

from vietnam_legal_rag.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

class GraphQuerier:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def get_document_amendments(self, document_number: str) -> List[Dict[str, Any]]:
        """Find all articles that amend a specific document (1 hop)."""
        query = """
        MATCH (a:Article)-[:AMENDS]->(d:LegalDocument {number: $doc_number})
        RETURN a.id AS amending_article, a.content AS content
        """
        return self.client.execute_query(query, {"doc_number": document_number})

    def get_related_documents(self, article_id: str) -> List[Dict[str, Any]]:
        """Find documents related to an article up to 2 hops away.
        For example: Article -> REFERS_TO -> Document <- AMENDS <- OtherArticle
        """
        query = """
        MATCH (a:Article {id: $art_id})-[:REFERS_TO]->(d:LegalDocument)<-[:AMENDS]-(other:Article)
        RETURN d.number AS referenced_doc, other.id AS amending_article
        """
        return self.client.execute_query(query, {"art_id": article_id})

    def get_document_hierarchy(self, document_number: str) -> List[Dict[str, Any]]:
        """Get the full hierarchy: Document and all its Articles."""
        query = """
        MATCH (d:LegalDocument {number: $doc_number})-[:CONTAINS]->(a:Article)
        RETURN d.title AS doc_title, a.number AS article_number, a.chapter AS chapter
        ORDER BY a.number
        """
        return self.client.execute_query(query, {"doc_number": document_number})

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    with Neo4jClient() as client:
        querier = GraphQuerier(client)
        
        # Test a query
        # Since we processed random 100 documents, let's just pick one document 
        # to see if it has relations. Let's find any document that is REFERS_TO.
        query_find = "MATCH (a:Article)-[:REFERS_TO]->(d:LegalDocument) RETURN d.number LIMIT 1"
        res = client.execute_query(query_find)
        if res:
            doc_number = res[0]["d.number"]
            logger.info(f"Found document with references: {doc_number}")
            refs = client.execute_query("MATCH (a:Article)-[:REFERS_TO]->(d:LegalDocument {number: $doc_number}) RETURN a.id LIMIT 5", {"doc_number": doc_number})
            logger.info(f"References to it from articles: {refs}")
        else:
            logger.info("No REFERS_TO relationships found in the current graph subset.")
