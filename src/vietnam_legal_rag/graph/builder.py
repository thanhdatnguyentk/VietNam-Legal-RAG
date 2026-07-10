"""Builder for the Legal Knowledge Graph."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List

from tqdm import tqdm

from vietnam_legal_rag.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client

    def build_from_chunks(self, chunks_file: Path):
        """Build graph from a processed chunks jsonl file."""
        logger.info(f"Building graph from {chunks_file}")
        
        with open(chunks_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in tqdm(lines, desc="Ingesting nodes"):
            if not line.strip():
                continue
            chunk = json.loads(line)
            metadata = chunk.get("metadata", {})
            self._process_chunk(chunk, metadata)
            
        # Optional: Second pass for relationship extraction
        self._extract_relations()

    def _process_chunk(self, chunk: Dict[str, Any], metadata: Dict[str, Any]):
        """Create nodes for Document and Article."""
        doc_number = metadata.get("document_number")
        doc_title = metadata.get("document_title")
        doc_id = metadata.get("doc_id")
        
        if not doc_number or not doc_id:
            return
            
        # Upsert Document node
        query_doc = """
        MERGE (d:LegalDocument {id: $doc_id})
        ON CREATE SET d.number = $doc_number,
                      d.title = $doc_title
        """
        self.client.execute_query(query_doc, {
            "doc_id": doc_id,
            "doc_number": doc_number,
            "doc_title": doc_title or ""
        })

        article = metadata.get("article")
        chapter = metadata.get("chapter")
        content = chunk.get("content", "")
        
        # If chunk is an article, create Article node
        if article:
            article_id = f"{doc_id}_art_{article}"
            query_art = """
            MERGE (a:Article {id: $art_id})
            ON CREATE SET a.number = $article,
                          a.chapter = $chapter,
                          a.content = $content
            """
            self.client.execute_query(query_art, {
                "art_id": article_id,
                "article": article,
                "chapter": chapter or "",
                "content": content
            })
            
            # Link Article to Document
            query_link = """
            MATCH (d:LegalDocument {id: $doc_id})
            MATCH (a:Article {id: $art_id})
            MERGE (d)-[:CONTAINS]->(a)
            """
            self.client.execute_query(query_link, {
                "doc_id": doc_id,
                "art_id": article_id
            })

    def _extract_relations(self):
        """Extract relationships using regex on article content."""
        logger.info("Extracting relationships (REFERS_TO, AMENDS, REPLACES)...")
        # Run a query to find documents/articles matching certain keywords
        # 1. Căn cứ
        query_refers_to = """
        MATCH (a:Article)
        WHERE a.content CONTAINS "Căn cứ" OR a.content CONTAINS "căn cứ"
        WITH a, a.content AS text
        // Simple heuristic: Link to Document if we find "Luật số", "Nghị định số", etc.
        // For production, this requires better NLP.
        MATCH (d:LegalDocument)
        WHERE text CONTAINS d.number
        MERGE (a)-[:REFERS_TO]->(d)
        """
        
        # 2. Sửa đổi, bổ sung
        query_amends = """
        MATCH (a:Article)
        WHERE a.content CONTAINS "Sửa đổi" OR a.content CONTAINS "sửa đổi" OR a.content CONTAINS "Bổ sung" OR a.content CONTAINS "bổ sung"
        WITH a, a.content AS text
        MATCH (d:LegalDocument)
        WHERE text CONTAINS d.number
        MERGE (a)-[:AMENDS]->(d)
        """
        
        # 3. Thay thế
        query_replaces = """
        MATCH (a:Article)
        WHERE a.content CONTAINS "Thay thế" OR a.content CONTAINS "thay thế"
        WITH a, a.content AS text
        MATCH (d:LegalDocument)
        WHERE text CONTAINS d.number
        MERGE (a)-[:REPLACES]->(d)
        """
        
        for q, name in [(query_refers_to, "REFERS_TO"), (query_amends, "AMENDS"), (query_replaces, "REPLACES")]:
            try:
                self.client.execute_query(q)
                logger.info(f"Executed {name} relation extraction.")
            except Exception as e:
                logger.warning(f"Failed to extract relations for {name}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from vietnam_legal_rag.paths import PROCESSED_DIR
    
    with Neo4jClient() as client:
        client.setup_schema()
        builder = GraphBuilder(client)
        import itertools
        
        # Process a few chunk files
        all_files = list(PROCESSED_DIR.rglob("*.chunks.jsonl"))
        num_files = min(100, len(all_files))
        logger.info(f"Found {len(all_files)} chunk files. Processing first {num_files}...")
        
        for test_file in all_files[:num_files]:
            builder.build_from_chunks(test_file)
