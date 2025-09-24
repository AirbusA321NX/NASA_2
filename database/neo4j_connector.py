from neo4j import GraphDatabase
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jConnector:
    """
    Neo4j connector for storing knowledge graph triples with provenance
    """
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    def connect(self):
        """
        Establish connection to Neo4j database
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database successfully")
        except Exception as e:
            logger.error(f"Error connecting to Neo4j: {e}")
            raise

    def disconnect(self):
        """
        Close connection to Neo4j database
        """
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j database")

    def initialize_schema(self):
        """
        Initialize Neo4j schema with constraints and indexes
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                # Create constraints for unique entity IDs
                session.run("""
                    CREATE CONSTRAINT entity_id_unique IF NOT EXISTS 
                    FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE
                """)
                
                # Create constraints for unique paper IDs
                session.run("""
                    CREATE CONSTRAINT paper_id_unique IF NOT EXISTS 
                    FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE
                """)
                
                # Create indexes for faster lookups
                session.run("""
                    CREATE INDEX entity_type_index IF NOT EXISTS 
                    FOR (e:Entity) ON (e.entity_type)
                """)
                
                session.run("""
                    CREATE INDEX entity_normalized_id_index IF NOT EXISTS 
                    FOR (e:Entity) ON (e.normalized_id)
                """)
                
                session.run("""
                    CREATE INDEX paper_doi_index IF NOT EXISTS 
                    FOR (p:Paper) ON (p.doi)
                """)
                
                # Create index for relationship predicates
                session.run("""
                    CREATE INDEX relationship_predicate_index IF NOT EXISTS 
                    FOR ()-[r:RELATIONSHIP]->() ON (r.predicate)
                """)
                
            logger.info("Neo4j schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Neo4j schema: {e}")
            raise

    def store_entities(self, entities: List[Dict[str, Any]]) -> int:
        """
        Store entities in Neo4j database
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Number of entities stored
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                # Use UNWIND to process multiple entities in a single query
                query = """
                UNWIND $entities AS entity
                MERGE (e:Entity {entity_id: entity.entity_id})
                SET e.entity_type = entity.entity_type,
                    e.entity_name = entity.entity_name,
                    e.normalized_id = entity.normalized_id,
                    e.normalized_name = entity.normalized_name,
                    e.confidence_score = entity.confidence_score,
                    e.paper_id = entity.paper_id,
                    e.sentence_id = entity.sentence_id,
                    e.updated_at = datetime()
                """
                
                result = session.run(query, entities=entities)
                # Get the count of processed entities
                count = len(entities)
                
            logger.info(f"Stored {count} entities in Neo4j")
            return count
            
        except Exception as e:
            logger.error(f"Error storing entities in Neo4j: {e}")
            raise

    def store_relationships(self, relationships: List[Dict[str, Any]]) -> int:
        """
        Store relationships in Neo4j database
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            Number of relationships stored
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                # Use UNWIND to process multiple relationships in a single query
                query = """
                UNWIND $relationships AS rel
                MATCH (subject:Entity {entity_id: rel.subject_id})
                MATCH (object:Entity {entity_id: rel.object_id})
                MERGE (subject)-[r:RELATIONSHIP {predicate: rel.predicate}]->(object)
                SET r.confidence_score = rel.confidence_score,
                    r.sentence_ids = rel.sentence_ids,
                    r.paper_ids = rel.paper_ids,
                    r.updated_at = datetime()
                """
                
                result = session.run(query, relationships=relationships)
                # Get the count of processed relationships
                count = len(relationships)
                
            logger.info(f"Stored {count} relationships in Neo4j")
            return count
            
        except Exception as e:
            logger.error(f"Error storing relationships in Neo4j: {e}")
            raise

    def store_papers(self, papers: List[Dict[str, Any]]) -> int:
        """
        Store paper metadata in Neo4j database
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Number of papers stored
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                # Use UNWIND to process multiple papers in a single query
                query = """
                UNWIND $papers AS paper
                MERGE (p:Paper {paper_id: paper.paper_id})
                SET p.title = paper.title,
                    p.authors = paper.authors,
                    p.abstract = paper.abstract,
                    p.year = paper.year,
                    p.doi = paper.doi,
                    p.osd_id = paper.osd_id,
                    p.nslsl_id = paper.nslsl_id,
                    p.pdf_url = paper.pdf_url,
                    p.keywords = paper.keywords,
                    p.publication_date = paper.publication_date,
                    p.updated_at = datetime()
                """
                
                result = session.run(query, papers=papers)
                # Get the count of processed papers
                count = len(papers)
                
            logger.info(f"Stored {count} papers in Neo4j")
            return count
            
        except Exception as e:
            logger.error(f"Error storing papers in Neo4j: {e}")
            raise

    def store_knowledge_graph(self, 
                            entities: List[Dict[str, Any]], 
                            relationships: List[Dict[str, Any]],
                            papers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, int]:
        """
        Store complete knowledge graph in Neo4j database
        
        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
            papers: Optional list of paper dictionaries
            
        Returns:
            Dictionary with counts of stored items
        """
        results = {}
        
        # Store papers first if provided
        if papers:
            results['papers'] = self.store_papers(papers)
            
        # Store entities
        results['entities'] = self.store_entities(entities)
        
        # Store relationships
        results['relationships'] = self.store_relationships(relationships)
        
        logger.info(f"Knowledge graph stored: {results}")
        return results

    def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve entity by ID
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity dictionary or None if not found
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {entity_id: $entity_id})
                    RETURN e
                """, entity_id=entity_id)
                
                record = result.single()
                if record:
                    node = record["e"]
                    return {
                        "entity_id": node["entity_id"],
                        "entity_type": node["entity_type"],
                        "entity_name": node["entity_name"],
                        "normalized_id": node.get("normalized_id"),
                        "normalized_name": node.get("normalized_name"),
                        "confidence_score": node.get("confidence_score", 0.0),
                        "paper_id": node.get("paper_id"),
                        "sentence_id": node.get("sentence_id")
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving entity from Neo4j: {e}")
            raise

    def get_relationships_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all relationships for a specific entity
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of relationship dictionaries
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {entity_id: $entity_id})-[r:RELATIONSHIP]-(other)
                    RETURN e.entity_id AS subject_id, 
                           r.predicate AS predicate,
                           other.entity_id AS object_id,
                           r.confidence_score AS confidence_score,
                           r.sentence_ids AS sentence_ids,
                           r.paper_ids AS paper_ids
                """, entity_id=entity_id)
                
                relationships = []
                for record in result:
                    relationships.append({
                        "subject_id": record["subject_id"],
                        "predicate": record["predicate"],
                        "object_id": record["object_id"],
                        "confidence_score": record["confidence_score"],
                        "sentence_ids": record["sentence_ids"] or [],
                        "paper_ids": record["paper_ids"] or []
                    })
                    
                return relationships
                
        except Exception as e:
            logger.error(f"Error retrieving relationships from Neo4j: {e}")
            raise

    def search_entities(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for entities by name or normalized name
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of entity dictionaries
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE toLower(e.entity_name) CONTAINS toLower($query)
                       OR toLower(e.normalized_name) CONTAINS toLower($query)
                    RETURN e
                    LIMIT $limit
                """, query=query, limit=limit)
                
                entities = []
                for record in result:
                    node = record["e"]
                    entities.append({
                        "entity_id": node["entity_id"],
                        "entity_type": node["entity_type"],
                        "entity_name": node["entity_name"],
                        "normalized_id": node.get("normalized_id"),
                        "normalized_name": node.get("normalized_name"),
                        "confidence_score": node.get("confidence_score", 0.0),
                        "paper_id": node.get("paper_id"),
                        "sentence_id": node.get("sentence_id")
                    })
                    
                return entities
                
        except Exception as e:
            logger.error(f"Error searching entities in Neo4j: {e}")
            raise

    def get_kg_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph
        
        Returns:
            Dictionary with KG statistics
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                # Get entity count
                entity_count = session.run("MATCH (e:Entity) RETURN count(e) AS count").single()["count"]
                
                # Get relationship count
                relationship_count = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) AS count").single()["count"]
                
                # Get paper count
                paper_count = session.run("MATCH (p:Paper) RETURN count(p) AS count").single()["count"]
                
                # Get entity type distribution
                type_distribution = session.run("""
                    MATCH (e:Entity)
                    RETURN e.entity_type AS type, count(e) AS count
                    ORDER BY count DESC
                """)
                
                type_dist = [{"type": record["type"], "count": record["count"]} for record in type_distribution]
                
                # Get relationship predicate distribution
                predicate_distribution = session.run("""
                    MATCH ()-[r:RELATIONSHIP]->()
                    RETURN r.predicate AS predicate, count(r) AS count
                    ORDER BY count DESC
                """)
                
                predicate_dist = [{"predicate": record["predicate"], "count": record["count"]} for record in predicate_distribution]
                
                return {
                    "entities": entity_count,
                    "relationships": relationship_count,
                    "papers": paper_count,
                    "entity_types": type_dist,
                    "relationship_predicates": predicate_dist
                }
                
        except Exception as e:
            logger.error(f"Error getting KG statistics from Neo4j: {e}")
            raise

    def delete_kg_data(self, paper_id: Optional[str] = None) -> Dict[str, int]:
        """
        Delete knowledge graph data, optionally filtered by paper ID
        
        Args:
            paper_id: Optional paper ID to filter deletion
            
        Returns:
            Dictionary with counts of deleted items
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j database")
            
        try:
            with self.driver.session() as session:
                if paper_id:
                    # Delete data for specific paper
                    rel_result = session.run("""
                        MATCH (e:Entity {paper_id: $paper_id})-[r:RELATIONSHIP]->()
                        DELETE r
                        RETURN count(r) AS count
                    """, paper_id=paper_id)
                    deleted_relationships = rel_result.single()["count"]
                    
                    ent_result = session.run("""
                        MATCH (e:Entity {paper_id: $paper_id})
                        DELETE e
                        RETURN count(e) AS count
                    """, paper_id=paper_id)
                    deleted_entities = ent_result.single()["count"]
                    
                    paper_result = session.run("""
                        MATCH (p:Paper {paper_id: $paper_id})
                        DELETE p
                        RETURN count(p) AS count
                    """, paper_id=paper_id)
                    deleted_papers = paper_result.single()["count"]
                else:
                    # Delete all data
                    rel_result = session.run("MATCH ()-[r:RELATIONSHIP]->() DELETE r RETURN count(r) AS count")
                    deleted_relationships = rel_result.single()["count"]
                    
                    ent_result = session.run("MATCH (e:Entity) DELETE e RETURN count(e) AS count")
                    deleted_entities = ent_result.single()["count"]
                    
                    paper_result = session.run("MATCH (p:Paper) DELETE p RETURN count(p) AS count")
                    deleted_papers = paper_result.single()["count"]
                
                return {
                    "relationships": deleted_relationships,
                    "entities": deleted_entities,
                    "papers": deleted_papers
                }
                
        except Exception as e:
            logger.error(f"Error deleting KG data from Neo4j: {e}")
            raise

def main():
    """
    Main function to demonstrate Neo4j connector functionality
    """
    # Initialize connector
    connector = Neo4jConnector(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    try:
        # Connect to database
        connector.connect()
        
        # Initialize schema
        connector.initialize_schema()
        
        # Example data
        example_papers = [
            {
                "paper_id": "paper_1",
                "title": "Effects of Microgravity on Plant Growth",
                "authors": ["Smith, J.", "Johnson, A."],
                "abstract": "This study examines the effects of microgravity on Arabidopsis thaliana growth.",
                "year": 2023,
                "doi": "10.1234/5678",
                "osd_id": "OSD-123",
                "nslsl_id": None,
                "pdf_url": "https://example.com/paper1.pdf",
                "keywords": ["microgravity", "plant growth", "Arabidopsis"],
                "publication_date": "2023-06-15"
            }
        ]
        
        example_entities = [
            {
                "entity_id": "ent_1",
                "entity_type": "organism",
                "entity_name": "Arabidopsis thaliana",
                "normalized_id": "NCBITaxon:3702",
                "normalized_name": "Arabidopsis thaliana",
                "confidence_score": 0.95,
                "paper_id": "paper_1",
                "sentence_id": "sent_1"
            },
            {
                "entity_id": "ent_2",
                "entity_type": "phenotype",
                "entity_name": "root growth",
                "normalized_id": "GO:0048468",
                "normalized_name": "cell development",
                "confidence_score": 0.85,
                "paper_id": "paper_1",
                "sentence_id": "sent_1"
            }
        ]
        
        example_relationships = [
            {
                "subject_id": "ent_1",
                "predicate": "shows",
                "object_id": "ent_2",
                "confidence_score": 0.9,
                "sentence_ids": ["sent_1"],
                "paper_ids": ["paper_1"]
            }
        ]
        
        # Store knowledge graph
        results = connector.store_knowledge_graph(
            entities=example_entities,
            relationships=example_relationships,
            papers=example_papers
        )
        print(f"Stored knowledge graph: {results}")
        
        # Get statistics
        stats = connector.get_kg_statistics()
        print(f"KG statistics: {stats}")
        
        # Search entities
        search_results = connector.search_entities("Arabidopsis")
        print(f"Search results: {search_results}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        # Disconnect
        connector.disconnect()

if __name__ == "__main__":
    main()