"""Neo4j Client for connecting to the Knowledge Graph."""

import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "VietLegal123"):
        self._driver: Optional[Driver] = None
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        if self._driver:
            self._driver.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return the results as a list of dictionaries."""
        if not self._driver:
            raise RuntimeError("Neo4j driver is not initialized")
        
        with self._driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def setup_schema(self):
        """Create constraints and indexes."""
        queries = [
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:LegalDocument) REQUIRE d.id IS UNIQUE;",
            "CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE;",
            "CREATE INDEX document_number IF NOT EXISTS FOR (d:LegalDocument) ON (d.number);"
        ]
        
        for q in queries:
            try:
                self.execute_query(q)
            except Exception as e:
                logger.warning(f"Failed to execute schema query: {q} - {e}")
                
        logger.info("Neo4j schema setup complete.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
