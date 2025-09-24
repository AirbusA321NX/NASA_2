import spacy
import logging
from typing import List, Dict, Any, Optional, Set
import re
from dataclasses import dataclass
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Data class for extracted entities"""
    entity_id: str
    entity_type: str
    entity_name: str
    normalized_id: Optional[str] = None
    normalized_name: Optional[str] = None
    confidence_score: float = 0.0
    sentence_id: Optional[str] = None
    paper_id: Optional[str] = None

@dataclass
class Relationship:
    """Data class for extracted relationships"""
    subject_id: str
    predicate: str
    object_id: str
    confidence_score: float = 0.0
    sentence_ids: List[str] = None
    paper_ids: List[str] = None
    
    def __post_init__(self):
        if self.sentence_ids is None:
            self.sentence_ids = []
        if self.paper_ids is None:
            self.paper_ids = []

class NERExtractor:
    """
    SciSpacy/rule-based NER for fact and KG extraction from Results/Conclusions chunks
    """
    
    def __init__(self):
        self.nlp = None
        self.entity_types = {
            'organism': ['ORGANISM', 'SPECIES', 'TAXON'],
            'phenotype': ['PHENOTYPE', 'TRAIT', 'CHARACTERISTIC'],
            'assay': ['ASSAY', 'EXPERIMENT', 'TEST', 'METHOD'],
            'platform': ['PLATFORM', 'INSTRUMENT', 'DEVICE', 'SYSTEM'],
            'outcome': ['OUTCOME', 'RESULT', 'FINDING', 'CONCLUSION']
        }
        
        # Define controlled vocabularies for normalization
        self.controlled_vocabularies = {
            'ncbi_taxon': {
                'arabidopsis': 'NCBITaxon:3702',
                'thaliana': 'NCBITaxon:3702',
                'arabidopsis thaliana': 'NCBITaxon:3702',
                'human': 'NCBITaxon:9606',
                'homo sapiens': 'NCBITaxon:9606',
                'mouse': 'NCBITaxon:10090',
                'mus musculus': 'NCBITaxon:10090',
                'fruit fly': 'NCBITaxon:7227',
                'drosophila': 'NCBITaxon:7227',
                'drosophila melanogaster': 'NCBITaxon:7227',
                'yeast': 'NCBITaxon:4932',
                'saccharomyces cerevisiae': 'NCBITaxon:4932',
                'e. coli': 'NCBITaxon:562',
                'escherichia coli': 'NCBITaxon:562',
                'c. elegans': 'NCBITaxon:6239',
                'caenorhabditis elegans': 'NCBITaxon:6239'
            },
            'go_terms': {
                'growth': 'GO:0040007',
                'development': 'GO:0032502',
                'expression': 'GO:0010467',
                'regulation': 'GO:0050789',
                'response': 'GO:0050896',
                'adaptation': 'GO:0032502'
            }
        }
        
        # Define relationship patterns
        self.relationship_patterns = [
            # Pattern: ORGANISM shows PHENOTYPE
            (r'(\w+(?:\s+\w+)*)\s+(?:shows?|exhibits?|demonstrates?|displays?)\s+(?:significant\s+)?(\w+(?:\s+\w+)*)', 
             'organism', 'shows', 'phenotype'),
            
            # Pattern: ASSAY measures PHENOTYPE
            (r'(\w+(?:\s+\w+)*)\s+(?:measures?|assesses?|evaluates?|quantifies?)\s+(?:the\s+)?(\w+(?:\s+\w+)*)', 
             'assay', 'measures', 'phenotype'),
            
            # Pattern: PLATFORM used for ASSAY
            (r'(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:used|employed|utilized)\s+(?:for|in)\s+(?:the\s+)?(\w+(?:\s+\w+)*)', 
             'platform', 'used_for', 'assay'),
            
            # Pattern: ORGANISM exposed to CONDITION shows OUTCOME
            (r'(\w+(?:\s+\w+)*)\s+(?:exposed|subjected)\s+to\s+(\w+(?:\s+\w+)*)\s+(?:shows?|exhibits?|demonstrates?)\s+(?:significant\s+)?(\w+(?:\s+\w+)*)', 
             'organism', 'shows_under_condition', 'outcome'),
        ]
        
        # Initialize spaCy model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the SciSpacy model"""
        try:
            # Try to load SciSpacy model
            self.nlp = spacy.load("en_core_sci_md")
            logger.info("Loaded SciSpacy model successfully")
        except OSError:
            try:
                # Fallback to regular spaCy model
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model successfully")
            except OSError:
                logger.warning("No spaCy model found. Please install with: python -m spacy download en_core_sci_md")
                self.nlp = None
        except Exception as e:
            logger.error(f"Error loading NLP model: {e}")
            self.nlp = None

    def extract_entities(self, text: str, paper_id: Optional[str] = None) -> List[Entity]:
        """
        Extract entities from text using SciSpacy and rule-based approaches
        
        Args:
            text: Input text to extract entities from
            paper_id: Optional paper ID for provenance tracking
            
        Returns:
            List of extracted entities
        """
        if not self.nlp:
            logger.warning("NLP model not available. Returning empty entity list.")
            return []
            
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            entities = []
            
            # Extract named entities from spaCy
            for ent in doc.ents:
                entity_type = self._map_entity_type(ent.label_)
                if entity_type:
                    entity = Entity(
                        entity_id=f"ent_{len(entities)}",
                        entity_type=entity_type,
                        entity_name=ent.text.strip(),
                        confidence_score=0.8,  # Confidence from NER model
                        paper_id=paper_id
                    )
                    entities.append(entity)
            
            # Apply rule-based extraction for additional entities
            rule_entities = self._extract_rule_based_entities(text, paper_id)
            entities.extend(rule_entities)
            
            # Normalize entities to controlled vocabularies
            normalized_entities = self._normalize_entities(entities)
            
            return normalized_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []

    def _map_entity_type(self, spacy_label: str) -> Optional[str]:
        """
        Map spaCy entity labels to our entity types
        
        Args:
            spacy_label: spaCy entity label
            
        Returns:
            Mapped entity type or None
        """
        # Map common spaCy/SciSpacy labels
        label_mapping = {
            'ORGANISM': 'organism',
            'SPECIES': 'organism',
            'TAXON': 'organism',
            'DISEASE': 'phenotype',
            'CHEMICAL': 'phenotype',
            'GENE': 'phenotype',
            'PROTEIN': 'phenotype',
            'CELL_TYPE': 'phenotype',
            'TISSUE': 'phenotype',
            'METHOD': 'assay',
            'DEVICE': 'platform',
            'SOFTWARE': 'platform'
        }
        
        return label_mapping.get(spacy_label)

    def _extract_rule_based_entities(self, text: str, paper_id: Optional[str] = None) -> List[Entity]:
        """
        Extract entities using rule-based patterns
        
        Args:
            text: Input text
            paper_id: Optional paper ID
            
        Returns:
            List of rule-based entities
        """
        entities = []
        
        # Common organisms in space biology
        organism_patterns = [
            (r'\b(?:arabidopsis(?:\s+thaliana)?|thale\s+cress)\b', 'organism', 'Arabidopsis thaliana'),
            (r'\b(?:human(?:s)?|homo\s+sapiens)\b', 'organism', 'Homo sapiens'),
            (r'\b(?:mouse|mice|mus\s+musculus)\b', 'organism', 'Mus musculus'),
            (r'\b(?:fruit\s+fly|drosophila(?:\s+melanogaster)?)\b', 'organism', 'Drosophila melanogaster'),
            (r'\b(?:yeast|saccharomyces(?:\s+cerevisiae)?)\b', 'organism', 'Saccharomyces cerevisiae'),
            (r'\b(?:e\.?\s*coli|escherichia\s+coli)\b', 'organism', 'Escherichia coli'),
            (r'\b(?:c\.?\s*elegans|caenorhabditis\s+elegans)\b', 'organism', 'Caenorhabditis elegans')
        ]
        
        # Extract organisms
        for pattern, entity_type, entity_name in organism_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    entity_id=f"rule_ent_{len(entities)}",
                    entity_type=entity_type,
                    entity_name=entity_name,
                    confidence_score=0.9,  # High confidence for rule-based matches
                    paper_id=paper_id
                )
                entities.append(entity)
        
        # Common space biology terms
        phenotype_patterns = [
            (r'\b(?:growth|development|expression|regulation|response|adaptation)\b', 'phenotype'),
            (r'\b(?:morphology|physiology|metabolism|gene\s+expression|protein\s+levels)\b', 'phenotype')
        ]
        
        # Extract phenotypes
        for pattern, entity_type in phenotype_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    entity_id=f"rule_ent_{len(entities)}",
                    entity_type=entity_type,
                    entity_name=match.group().strip(),
                    confidence_score=0.7,
                    paper_id=paper_id
                )
                entities.append(entity)
        
        return entities

    def _normalize_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Normalize entities to controlled vocabularies
        
        Args:
            entities: List of entities to normalize
            
        Returns:
            List of normalized entities
        """
        normalized_entities = []
        
        for entity in entities:
            normalized_entity = Entity(
                entity_id=entity.entity_id,
                entity_type=entity.entity_type,
                entity_name=entity.entity_name,
                confidence_score=entity.confidence_score,
                paper_id=entity.paper_id
            )
            
            # Normalize based on entity type
            if entity.entity_type == 'organism':
                normalized = self._normalize_organism(entity.entity_name)
                if normalized:
                    normalized_entity.normalized_id = normalized['id']
                    normalized_entity.normalized_name = normalized['name']
                    
            elif entity.entity_type == 'phenotype':
                normalized = self._normalize_phenotype(entity.entity_name)
                if normalized:
                    normalized_entity.normalized_id = normalized['id']
                    normalized_entity.normalized_name = normalized['name']
            
            normalized_entities.append(normalized_entity)
            
        return normalized_entities

    def _normalize_organism(self, organism_name: str) -> Optional[Dict[str, str]]:
        """
        Normalize organism name to NCBI taxonomy
        
        Args:
            organism_name: Organism name to normalize
            
        Returns:
            Dictionary with normalized ID and name, or None
        """
        organism_lower = organism_name.lower()
        
        # Check controlled vocabulary
        for name, taxon_id in self.controlled_vocabularies['ncbi_taxon'].items():
            if name in organism_lower:
                return {
                    'id': taxon_id,
                    'name': name.title()
                }
                
        return None

    def _normalize_phenotype(self, phenotype_name: str) -> Optional[Dict[str, str]]:
        """
        Normalize phenotype name to GO terms
        
        Args:
            phenotype_name: Phenotype name to normalize
            
        Returns:
            Dictionary with normalized ID and name, or None
        """
        phenotype_lower = phenotype_name.lower()
        
        # Check controlled vocabulary
        for term, go_id in self.controlled_vocabularies['go_terms'].items():
            if term in phenotype_lower:
                return {
                    'id': go_id,
                    'name': term.title()
                }
                
        return None

    def extract_relationships(self, text: str, entities: List[Entity], 
                            paper_id: Optional[str] = None) -> List[Relationship]:
        """
        Extract relationships between entities using patterns
        
        Args:
            text: Input text
            entities: List of entities in the text
            paper_id: Optional paper ID
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Apply relationship patterns
        for pattern, subj_type, predicate, obj_type in self.relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                subject_text = match.group(1).strip()
                object_text = match.group(2).strip()
                
                # Find matching entities
                subject_entity = self._find_entity_by_text(entities, subject_text, subj_type)
                object_entity = self._find_entity_by_text(entities, object_text, obj_type)
                
                if subject_entity and object_entity:
                    relationship = Relationship(
                        subject_id=subject_entity.entity_id,
                        predicate=predicate,
                        object_id=object_entity.entity_id,
                        confidence_score=0.8,
                        paper_ids=[paper_id] if paper_id else []
                    )
                    relationships.append(relationship)
        
        return relationships

    def _find_entity_by_text(self, entities: List[Entity], text: str, entity_type: str) -> Optional[Entity]:
        """
        Find entity by text and type
        
        Args:
            entities: List of entities to search
            text: Text to match
            entity_type: Entity type to match
            
        Returns:
            Matching entity or None
        """
        text_lower = text.lower()
        for entity in entities:
            if entity.entity_type == entity_type and text_lower in entity.entity_name.lower():
                return entity
        return None

    def extract_from_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Extract entities and relationships from document chunks
        
        Args:
            chunks: List of document chunks with content
            
        Returns:
            Dictionary with extracted entities and relationships
        """
        all_entities = []
        all_relationships = []
        
        for chunk in chunks:
            paper_id = chunk.get('paper_id')
            content = chunk.get('content', '')
            section_type = chunk.get('section_type', '')
            
            # Only process Results and Conclusions sections
            if section_type.lower() in ['results', 'conclusions']:
                # Extract entities
                entities = self.extract_entities(content, paper_id)
                all_entities.extend(entities)
                
                # Extract relationships
                relationships = self.extract_relationships(content, entities, paper_id)
                all_relationships.extend(relationships)
        
        return {
            'entities': all_entities,
            'relationships': all_relationships
        }

    def get_entity_statistics(self, entities: List[Entity]) -> Dict[str, Any]:
        """
        Get statistics about extracted entities
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary with entity statistics
        """
        stats = defaultdict(int)
        unique_entities = set()
        
        for entity in entities:
            stats[entity.entity_type] += 1
            unique_entities.add(entity.entity_name)
            
        return {
            'total_entities': len(entities),
            'unique_entities': len(unique_entities),
            'by_type': dict(stats)
        }

    def get_relationship_statistics(self, relationships: List[Relationship]) -> Dict[str, Any]:
        """
        Get statistics about extracted relationships
        
        Args:
            relationships: List of relationships
            
        Returns:
            Dictionary with relationship statistics
        """
        stats = defaultdict(int)
        unique_relationships = set()
        
        for relationship in relationships:
            stats[relationship.predicate] += 1
            unique_relationships.add((relationship.subject_id, relationship.predicate, relationship.object_id))
            
        return {
            'total_relationships': len(relationships),
            'unique_relationships': len(unique_relationships),
            'by_predicate': dict(stats)
        }

def main():
    """
    Main function to demonstrate NER extractor functionality
    """
    # Initialize extractor
    extractor = NERExtractor()
    
    # Example text
    example_text = """
    Arabidopsis thaliana plants grown in microgravity conditions showed significant changes in root growth patterns.
    Gene expression analysis using RNA-seq platform revealed differential expression of stress response genes.
    Mouse models subjected to cosmic radiation exposure exhibited increased DNA damage markers.
    The results demonstrate that microgravity significantly affects plant development and metabolism.
    """
    
    print("Example text:")
    print(example_text)
    
    # Extract entities
    entities = extractor.extract_entities(example_text, paper_id="paper_1")
    print(f"\nExtracted {len(entities)} entities:")
    for entity in entities:
        print(f"  {entity.entity_type}: {entity.entity_name} (confidence: {entity.confidence_score})")
        if entity.normalized_id:
            print(f"    Normalized: {entity.normalized_name} ({entity.normalized_id})")
    
    # Extract relationships
    relationships = extractor.extract_relationships(example_text, entities, paper_id="paper_1")
    print(f"\nExtracted {len(relationships)} relationships:")
    for rel in relationships:
        print(f"  {rel.subject_id} --{rel.predicate}--> {rel.object_id} (confidence: {rel.confidence_score})")
    
    # Statistics
    entity_stats = extractor.get_entity_statistics(entities)
    print(f"\nEntity statistics: {entity_stats}")
    
    relationship_stats = extractor.get_relationship_statistics(relationships)
    print(f"Relationship statistics: {relationship_stats}")

if __name__ == "__main__":
    main()