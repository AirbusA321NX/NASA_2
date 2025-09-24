import logging
from typing import Dict, List, Any, Optional
import requests
import time
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VocabularyNormalizer:
    """
    Normalize extracted entities to controlled vocabularies (NCBI taxon, GO/EDAM/OBI)
    """
    
    def __init__(self):
        # API endpoints for different vocabularies
        self.apis = {
            'ncbi_taxon': 'https://api.ncbi.nlm.nih.gov/datasets/v2alpha/taxonomy/taxon/',
            'go': 'https://www.ebi.ac.uk/ols/api/search?q=',
            'edam': 'https://www.ebi.ac.uk/ols/api/search?q=',
            'obi': 'https://www.ebi.ac.uk/ols/api/search?q='
        }
        
        # Controlled vocabulary mappings (expanded from NER extractor)
        self.local_vocabularies = {
            'ncbi_taxon': {
                # Plants
                'arabidopsis': {'id': 'NCBITaxon:3702', 'name': 'Arabidopsis thaliana'},
                'thaliana': {'id': 'NCBITaxon:3702', 'name': 'Arabidopsis thaliana'},
                'arabidopsis thaliana': {'id': 'NCBITaxon:3702', 'name': 'Arabidopsis thaliana'},
                'rice': {'id': 'NCBITaxon:39947', 'name': 'Oryza sativa'},
                'oryza sativa': {'id': 'NCBITaxon:39947', 'name': 'Oryza sativa'},
                'maize': {'id': 'NCBITaxon:4577', 'name': 'Zea mays'},
                'zea mays': {'id': 'NCBITaxon:4577', 'name': 'Zea mays'},
                
                # Humans
                'human': {'id': 'NCBITaxon:9606', 'name': 'Homo sapiens'},
                'homo sapiens': {'id': 'NCBITaxon:9606', 'name': 'Homo sapiens'},
                'humans': {'id': 'NCBITaxon:9606', 'name': 'Homo sapiens'},
                
                # Model organisms
                'mouse': {'id': 'NCBITaxon:10090', 'name': 'Mus musculus'},
                'mus musculus': {'id': 'NCBITaxon:10090', 'name': 'Mus musculus'},
                'mice': {'id': 'NCBITaxon:10090', 'name': 'Mus musculus'},
                'fruit fly': {'id': 'NCBITaxon:7227', 'name': 'Drosophila melanogaster'},
                'drosophila': {'id': 'NCBITaxon:7227', 'name': 'Drosophila melanogaster'},
                'drosophila melanogaster': {'id': 'NCBITaxon:7227', 'name': 'Drosophila melanogaster'},
                'yeast': {'id': 'NCBITaxon:4932', 'name': 'Saccharomyces cerevisiae'},
                'saccharomyces cerevisiae': {'id': 'NCBITaxon:4932', 'name': 'Saccharomyces cerevisiae'},
                'e. coli': {'id': 'NCBITaxon:562', 'name': 'Escherichia coli'},
                'escherichia coli': {'id': 'NCBITaxon:562', 'name': 'Escherichia coli'},
                'c. elegans': {'id': 'NCBITaxon:6239', 'name': 'Caenorhabditis elegans'},
                'caenorhabditis elegans': {'id': 'NCBITaxon:6239', 'name': 'Caenorhabditis elegans'},
                'bacteria': {'id': 'NCBITaxon:2', 'name': 'Bacteria'},
                'bacterial': {'id': 'NCBITaxon:2', 'name': 'Bacteria'},
                
                # Space-specific organisms
                'deinococcus radiodurans': {'id': 'NCBITaxon:12908', 'name': 'Deinococcus radiodurans'},
                'radiodurans': {'id': 'NCBITaxon:12908', 'name': 'Deinococcus radiodurans'},
                'synechococcus': {'id': 'NCBITaxon:1129', 'name': 'Synechococcus'},
                'cyanobacteria': {'id': 'NCBITaxon:1117', 'name': 'Cyanobacteria'}
            },
            
            'go_terms': {
                # Biological processes
                'growth': {'id': 'GO:0040007', 'name': 'growth'},
                'development': {'id': 'GO:0032502', 'name': 'developmental process'},
                'cell development': {'id': 'GO:0048468', 'name': 'cell development'},
                'organ development': {'id': 'GO:0048513', 'name': 'organ development'},
                'tissue development': {'id': 'GO:0009888', 'name': 'tissue development'},
                'morphogenesis': {'id': 'GO:0009653', 'name': 'anatomical structure morphogenesis'},
                'differentiation': {'id': 'GO:0030154', 'name': 'cell differentiation'},
                'cell differentiation': {'id': 'GO:0030154', 'name': 'cell differentiation'},
                'proliferation': {'id': 'GO:0008283', 'name': 'cell proliferation'},
                'cell proliferation': {'id': 'GO:0008283', 'name': 'cell proliferation'},
                
                # Molecular functions
                'expression': {'id': 'GO:0010467', 'name': 'gene expression'},
                'gene expression': {'id': 'GO:0010467', 'name': 'gene expression'},
                'transcription': {'id': 'GO:0006351', 'name': 'transcription, DNA-templated'},
                'translation': {'id': 'GO:0006412', 'name': 'translation'},
                'protein synthesis': {'id': 'GO:0006412', 'name': 'translation'},
                'metabolism': {'id': 'GO:0008152', 'name': 'metabolic process'},
                'metabolic process': {'id': 'GO:0008152', 'name': 'metabolic process'},
                'catabolism': {'id': 'GO:0009056', 'name': 'catabolic process'},
                'anabolism': {'id': 'GO:0009058', 'name': 'biosynthetic process'},
                'biosynthesis': {'id': 'GO:0009058', 'name': 'biosynthetic process'},
                'biosynthetic process': {'id': 'GO:0009058', 'name': 'biosynthetic process'},
                
                # Responses and regulations
                'response': {'id': 'GO:0050896', 'name': 'response to stimulus'},
                'response to stimulus': {'id': 'GO:0050896', 'name': 'response to stimulus'},
                'stress response': {'id': 'GO:0006950', 'name': 'response to stress'},
                'response to stress': {'id': 'GO:0006950', 'name': 'response to stress'},
                'dna damage response': {'id': 'GO:0006974', 'name': 'cellular response to DNA damage stimulus'},
                'oxidative stress response': {'id': 'GO:0006979', 'name': 'response to oxidative stress'},
                'regulation': {'id': 'GO:0050789', 'name': 'regulation of biological process'},
                'regulation of biological process': {'id': 'GO:0050789', 'name': 'regulation of biological process'},
                'signal transduction': {'id': 'GO:0007165', 'name': 'signal transduction'},
                
                # Space biology specific
                'gravity response': {'id': 'GO:0009625', 'name': 'response to gravity'},
                'response to gravity': {'id': 'GO:0009625', 'name': 'response to gravity'},
                'microgravity response': {'id': 'GO:0009625', 'name': 'response to gravity'},
                'radiation response': {'id': 'GO:0010212', 'name': 'response to ionizing radiation'},
                'ionizing radiation response': {'id': 'GO:0010212', 'name': 'response to ionizing radiation'}
            },
            
            'edam_terms': {
                # Data types
                'sequence data': {'id': 'data_2977', 'name': 'Sequence data'},
                'protein sequence': {'id': 'data_2976', 'name': 'Protein sequence'},
                'dna sequence': {'id': 'data_2974', 'name': 'DNA sequence'},
                'rna sequence': {'id': 'data_2975', 'name': 'RNA sequence'},
                'gene expression': {'id': 'data_2603', 'name': 'Gene expression data'},
                'expression data': {'id': 'data_2603', 'name': 'Gene expression data'},
                'microarray data': {'id': 'data_3110', 'name': 'Microarray data'},
                'proteomics data': {'id': 'data_2602', 'name': 'Proteomics data'},
                'metabolomics data': {'id': 'data_2601', 'name': 'Metabolomics data'},
                
                # Operations
                'sequence analysis': {'id': 'operation_2403', 'name': 'Sequence analysis'},
                'alignment': {'id': 'operation_2928', 'name': 'Alignment'},
                'sequence alignment': {'id': 'operation_2928', 'name': 'Alignment'},
                'phylogenetic analysis': {'id': 'operation_0324', 'name': 'Phylogenetic analysis'},
                'clustering': {'id': 'operation_3432', 'name': 'Clustering'},
                'classification': {'id': 'operation_2990', 'name': 'Classification'},
                'statistical analysis': {'id': 'operation_2425', 'name': 'Statistical analysis'},
                
                # Formats
                'fasta format': {'id': 'format_1929', 'name': 'FASTA format'},
                'fastq format': {'id': 'format_2330', 'name': 'FASTQ format'},
                'bam format': {'id': 'format_2572', 'name': 'BAM format'},
                'sam format': {'id': 'format_2573', 'name': 'SAM format'}
            },
            
            'obi_terms': {
                # Assays and instruments
                'microscopy': {'id': 'OBI:0000245', 'name': 'microscopy'},
                'fluorescence microscopy': {'id': 'OBI:0000246', 'name': 'fluorescence microscopy'},
                'confocal microscopy': {'id': 'OBI:0000247', 'name': 'confocal microscopy'},
                'electron microscopy': {'id': 'OBI:0000248', 'name': 'electron microscopy'},
                'spectroscopy': {'id': 'OBI:0000249', 'name': 'spectroscopy'},
                'mass spectrometry': {'id': 'OBI:0000250', 'name': 'mass spectrometry'},
                'flow cytometry': {'id': 'OBI:0000251', 'name': 'flow cytometry'},
                'pcr': {'id': 'OBI:0000252', 'name': 'PCR'},
                'real time pcr': {'id': 'OBI:0000253', 'name': 'real time PCR'},
                'western blot': {'id': 'OBI:0000254', 'name': 'western blot'},
                'northern blot': {'id': 'OBI:0000255', 'name': 'northern blot'},
                'southern blot': {'id': 'OBI:0000256', 'name': 'southern blot'},
                
                # Biological processes
                'culturing': {'id': 'OBI:0000257', 'name': 'culturing'},
                'cell culture': {'id': 'OBI:0000258', 'name': 'cell culture'},
                'transfection': {'id': 'OBI:0000259', 'name': 'transfection'},
                'transduction': {'id': 'OBI:0000260', 'name': 'transduction'}
            }
        }

    def normalize_entity(self, entity_name: str, entity_type: str) -> Optional[Dict[str, str]]:
        """
        Normalize a single entity to controlled vocabularies
        
        Args:
            entity_name: Name of the entity to normalize
            entity_type: Type of the entity (organism, phenotype, etc.)
            
        Returns:
            Dictionary with normalized ID and name, or None if not found
        """
        entity_name_lower = entity_name.lower().strip()
        
        # Try local vocabulary first
        if entity_type == 'organism':
            return self._normalize_ncbi_taxon(entity_name_lower)
        elif entity_type == 'phenotype':
            return self._normalize_go_term(entity_name_lower)
        elif entity_type == 'assay':
            return self._normalize_obi_term(entity_name_lower)
        elif entity_type == 'platform':
            # Platform could be in EDAM or OBI
            result = self._normalize_edam_term(entity_name_lower)
            if not result:
                result = self._normalize_obi_term(entity_name_lower)
            return result
            
        return None

    def _normalize_ncbi_taxon(self, organism_name: str) -> Optional[Dict[str, str]]:
        """
        Normalize organism name to NCBI taxonomy
        
        Args:
            organism_name: Organism name to normalize
            
        Returns:
            Dictionary with normalized ID and name, or None
        """
        # Check local vocabulary first
        for name, taxon_info in self.local_vocabularies['ncbi_taxon'].items():
            if name in organism_name:
                return taxon_info
                
        # If not found locally, try external API (simplified)
        # In a real implementation, you would call the NCBI API
        logger.debug(f"NCBI taxon not found locally for: {organism_name}")
        return None

    def _normalize_go_term(self, term_name: str) -> Optional[Dict[str, str]]:
        """
        Normalize term to Gene Ontology
        
        Args:
            term_name: Term name to normalize
            
        Returns:
            Dictionary with normalized ID and name, or None
        """
        # Check local vocabulary first
        for term, go_info in self.local_vocabularies['go_terms'].items():
            if term in term_name:
                return go_info
                
        # If not found locally, try external API (simplified)
        logger.debug(f"GO term not found locally for: {term_name}")
        return None

    def _normalize_edam_term(self, term_name: str) -> Optional[Dict[str, str]]:
        """
        Normalize term to EDAM ontology
        
        Args:
            term_name: Term name to normalize
            
        Returns:
            Dictionary with normalized ID and name, or None
        """
        # Check local vocabulary first
        for term, edam_info in self.local_vocabularies['edam_terms'].items():
            if term in term_name:
                return edam_info
                
        # If not found locally, try external API (simplified)
        logger.debug(f"EDAM term not found locally for: {term_name}")
        return None

    def _normalize_obi_term(self, term_name: str) -> Optional[Dict[str, str]]:
        """
        Normalize term to OBI ontology
        
        Args:
            term_name: Term name to normalize
            
        Returns:
            Dictionary with normalized ID and name, or None
        """
        # Check local vocabulary first
        for term, obi_info in self.local_vocabularies['obi_terms'].items():
            if term in term_name:
                return obi_info
                
        # If not found locally, try external API (simplified)
        logger.debug(f"OBI term not found locally for: {term_name}")
        return None

    def normalize_entities_batch(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a batch of entities to controlled vocabularies
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            List of normalized entity dictionaries
        """
        normalized_entities = []
        
        for entity in entities:
            # Create a copy to avoid modifying original
            normalized_entity = entity.copy()
            
            # Extract entity information
            entity_name = entity.get('entity_name', '')
            entity_type = entity.get('entity_type', '')
            
            # Normalize
            normalized_info = self.normalize_entity(entity_name, entity_type)
            
            if normalized_info:
                normalized_entity['normalized_id'] = normalized_info['id']
                normalized_entity['normalized_name'] = normalized_info['name']
                # Set high confidence for normalized entities
                normalized_entity['confidence_score'] = max(
                    entity.get('confidence_score', 0.5),
                    0.9  # High confidence for controlled vocabulary matches
                )
            else:
                # Keep original confidence if not normalized
                normalized_entity['confidence_score'] = entity.get('confidence_score', 0.5)
                
            normalized_entities.append(normalized_entity)
            
        return normalized_entities

    def get_normalization_statistics(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about entity normalization
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary with normalization statistics
        """
        total_entities = len(entities)
        normalized_entities = sum(1 for entity in entities if entity.get('normalized_id'))
        
        # Count by entity type
        type_stats = defaultdict(lambda: {'total': 0, 'normalized': 0})
        for entity in entities:
            entity_type = entity.get('entity_type', 'unknown')
            type_stats[entity_type]['total'] += 1
            if entity.get('normalized_id'):
                type_stats[entity_type]['normalized'] += 1
        
        return {
            'total_entities': total_entities,
            'normalized_entities': normalized_entities,
            'normalization_rate': normalized_entities / total_entities if total_entities > 0 else 0,
            'by_type': {
                entity_type: {
                    'total': stats['total'],
                    'normalized': stats['normalized'],
                    'normalization_rate': stats['normalized'] / stats['total'] if stats['total'] > 0 else 0
                }
                for entity_type, stats in type_stats.items()
            }
        }

    def expand_vocabulary(self, vocabulary_name: str, new_terms: Dict[str, Dict[str, str]]):
        """
        Expand local vocabulary with new terms
        
        Args:
            vocabulary_name: Name of the vocabulary to expand
            new_terms: Dictionary of new terms to add
        """
        if vocabulary_name in self.local_vocabularies:
            self.local_vocabularies[vocabulary_name].update(new_terms)
            logger.info(f"Expanded {vocabulary_name} vocabulary with {len(new_terms)} new terms")
        else:
            logger.warning(f"Unknown vocabulary: {vocabulary_name}")

def main():
    """
    Main function to demonstrate vocabulary normalizer functionality
    """
    # Initialize normalizer
    normalizer = VocabularyNormalizer()
    
    # Example entities
    example_entities = [
        {'entity_name': 'Arabidopsis thaliana', 'entity_type': 'organism', 'confidence_score': 0.8},
        {'entity_name': 'gene expression', 'entity_type': 'phenotype', 'confidence_score': 0.7},
        {'entity_name': 'microscopy', 'entity_type': 'platform', 'confidence_score': 0.6},
        {'entity_name': 'pcr', 'entity_type': 'assay', 'confidence_score': 0.9},
        {'entity_name': 'human', 'entity_type': 'organism', 'confidence_score': 0.85}
    ]
    
    print("Original entities:")
    for entity in example_entities:
        print(f"  {entity['entity_type']}: {entity['entity_name']} (confidence: {entity['confidence_score']})")
    
    # Normalize entities
    normalized_entities = normalizer.normalize_entities_batch(example_entities)
    
    print("\nNormalized entities:")
    for entity in normalized_entities:
        print(f"  {entity['entity_type']}: {entity['entity_name']} (confidence: {entity['confidence_score']})")
        if entity.get('normalized_id'):
            print(f"    -> {entity['normalized_name']} ({entity['normalized_id']})")
        else:
            print("    -> Not normalized")
    
    # Statistics
    stats = normalizer.get_normalization_statistics(normalized_entities)
    print(f"\nNormalization statistics: {stats}")

if __name__ == "__main__":
    main()