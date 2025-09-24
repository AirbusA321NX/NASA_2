import logging
import random
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationSample:
    """Data class for validation samples"""
    entity_id: str
    entity_name: str
    entity_type: str
    expected_normalized_id: Optional[str]
    expected_normalized_name: Optional[str]
    is_correct: Optional[bool] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None

@dataclass
class RelationshipValidationSample:
    """Data class for relationship validation samples"""
    subject_id: str
    predicate: str
    object_id: str
    is_correct: Optional[bool] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None

class KGValidator:
    """
    Automatic precision checks on held-out sample for KG validation
    """
    
    def __init__(self, validation_threshold: float = 0.8):
        self.validation_threshold = validation_threshold
        self.validation_samples = []
        self.relationship_validation_samples = []
        
    def create_entity_validation_samples(self, 
                                       entities: List[Dict[str, Any]], 
                                       sample_size: int = 100) -> List[ValidationSample]:
        """
        Create validation samples for entities by holding out a sample
        
        Args:
            entities: List of entity dictionaries
            sample_size: Number of samples to create
            
        Returns:
            List of validation samples
        """
        # Filter entities with normalization
        normalized_entities = [e for e in entities if e.get('normalized_id')]
        
        # If we don't have enough normalized entities, use all entities
        sample_entities = normalized_entities if len(normalized_entities) >= sample_size else entities
        
        # Randomly sample entities
        if len(sample_entities) > sample_size:
            sample_entities = random.sample(sample_entities, sample_size)
            
        # Create validation samples
        validation_samples = []
        for entity in sample_entities:
            sample = ValidationSample(
                entity_id=entity.get('entity_id', ''),
                entity_name=entity.get('entity_name', ''),
                entity_type=entity.get('entity_type', ''),
                expected_normalized_id=entity.get('normalized_id'),
                expected_normalized_name=entity.get('normalized_name'),
                confidence=entity.get('confidence_score', 0.0)
            )
            validation_samples.append(sample)
            
        self.validation_samples = validation_samples
        logger.info(f"Created {len(validation_samples)} entity validation samples")
        return validation_samples

    def create_relationship_validation_samples(self, 
                                            relationships: List[Dict[str, Any]], 
                                            sample_size: int = 50) -> List[RelationshipValidationSample]:
        """
        Create validation samples for relationships by holding out a sample
        
        Args:
            relationships: List of relationship dictionaries
            sample_size: Number of samples to create
            
        Returns:
            List of relationship validation samples
        """
        # Randomly sample relationships
        if len(relationships) > sample_size:
            sample_relationships = random.sample(relationships, sample_size)
        else:
            sample_relationships = relationships
            
        # Create validation samples
        validation_samples = []
        for rel in sample_relationships:
            sample = RelationshipValidationSample(
                subject_id=rel.get('subject_id', ''),
                predicate=rel.get('predicate', ''),
                object_id=rel.get('object_id', ''),
                confidence=rel.get('confidence_score', 0.0)
            )
            validation_samples.append(sample)
            
        self.relationship_validation_samples = validation_samples
        logger.info(f"Created {len(validation_samples)} relationship validation samples")
        return validation_samples

    def validate_entity_samples(self, 
                              validation_results: List[Tuple[str, bool, Optional[str]]]) -> Dict[str, Any]:
        """
        Validate entity samples and calculate precision metrics
        
        Args:
            validation_results: List of tuples (entity_id, is_correct, notes)
            
        Returns:
            Dictionary with validation metrics
        """
        # Create lookup dictionary
        results_lookup = {entity_id: (is_correct, notes) for entity_id, is_correct, notes in validation_results}
        
        # Update validation samples
        correct_count = 0
        total_count = 0
        
        for sample in self.validation_samples:
            if sample.entity_id in results_lookup:
                is_correct, notes = results_lookup[sample.entity_id]
                sample.is_correct = is_correct
                sample.notes = notes
                total_count += 1
                if is_correct:
                    correct_count += 1
                    
        # Calculate precision
        precision = correct_count / total_count if total_count > 0 else 0.0
        
        # Calculate precision by entity type
        type_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        for sample in self.validation_samples:
            if sample.is_correct is not None:
                type_stats[sample.entity_type]['total'] += 1
                if sample.is_correct:
                    type_stats[sample.entity_type]['correct'] += 1
                    
        type_precision = {
            entity_type: {
                'precision': stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0,
                'correct': stats['correct'],
                'total': stats['total']
            }
            for entity_type, stats in type_stats.items()
        }
        
        validation_report = {
            'total_samples': total_count,
            'correct_samples': correct_count,
            'precision': precision,
            'precision_by_type': type_precision,
            'validation_threshold': self.validation_threshold,
            'passed': precision >= self.validation_threshold
        }
        
        logger.info(f"Entity validation results: {validation_report}")
        return validation_report

    def validate_relationship_samples(self, 
                                    validation_results: List[Tuple[str, str, str, bool, Optional[str]]]) -> Dict[str, Any]:
        """
        Validate relationship samples and calculate precision metrics
        
        Args:
            validation_results: List of tuples (subject_id, predicate, object_id, is_correct, notes)
            
        Returns:
            Dictionary with validation metrics
        """
        # Create lookup dictionary (using a composite key)
        results_lookup = {
            (subj_id, pred, obj_id): (is_correct, notes) 
            for subj_id, pred, obj_id, is_correct, notes in validation_results
        }
        
        # Update validation samples
        correct_count = 0
        total_count = 0
        
        for sample in self.relationship_validation_samples:
            key = (sample.subject_id, sample.predicate, sample.object_id)
            if key in results_lookup:
                is_correct, notes = results_lookup[key]
                sample.is_correct = is_correct
                sample.notes = notes
                total_count += 1
                if is_correct:
                    correct_count += 1
                    
        # Calculate precision
        precision = correct_count / total_count if total_count > 0 else 0.0
        
        validation_report = {
            'total_samples': total_count,
            'correct_samples': correct_count,
            'precision': precision,
            'validation_threshold': self.validation_threshold,
            'passed': precision >= self.validation_threshold
        }
        
        logger.info(f"Relationship validation results: {validation_report}")
        return validation_report

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of current validation samples
        
        Returns:
            Dictionary with validation summary
        """
        # Entity validation summary
        entity_validated = [s for s in self.validation_samples if s.is_correct is not None]
        entity_correct = sum(1 for s in entity_validated if s.is_correct)
        entity_precision = entity_correct / len(entity_validated) if entity_validated else 0.0
        
        # Relationship validation summary
        rel_validated = [s for s in self.relationship_validation_samples if s.is_correct is not None]
        rel_correct = sum(1 for s in rel_validated if s.is_correct)
        rel_precision = rel_correct / len(rel_validated) if rel_validated else 0.0
        
        return {
            'entity_validation': {
                'total_samples': len(self.validation_samples),
                'validated_samples': len(entity_validated),
                'correct_samples': entity_correct,
                'precision': entity_precision
            },
            'relationship_validation': {
                'total_samples': len(self.relationship_validation_samples),
                'validated_samples': len(rel_validated),
                'correct_samples': rel_correct,
                'precision': rel_precision
            }
        }

    def save_validation_samples(self, filepath: str):
        """
        Save validation samples to file for manual review
        
        Args:
            filepath: Path to save validation samples
        """
        # Convert to serializable format
        entity_samples = []
        for sample in self.validation_samples:
            entity_samples.append({
                'entity_id': sample.entity_id,
                'entity_name': sample.entity_name,
                'entity_type': sample.entity_type,
                'expected_normalized_id': sample.expected_normalized_id,
                'expected_normalized_name': sample.expected_normalized_name,
                'is_correct': sample.is_correct,
                'confidence': sample.confidence,
                'notes': sample.notes
            })
            
        relationship_samples = []
        for sample in self.relationship_validation_samples:
            relationship_samples.append({
                'subject_id': sample.subject_id,
                'predicate': sample.predicate,
                'object_id': sample.object_id,
                'is_correct': sample.is_correct,
                'confidence': sample.confidence,
                'notes': sample.notes
            })
            
        data = {
            'entity_samples': entity_samples,
            'relationship_samples': relationship_samples,
            'created_at': __import__('datetime').datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Saved validation samples to {filepath}")

    def load_validation_samples(self, filepath: str):
        """
        Load validation samples from file
        
        Args:
            filepath: Path to load validation samples from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Load entity samples
        self.validation_samples = []
        for sample_data in data.get('entity_samples', []):
            sample = ValidationSample(
                entity_id=sample_data['entity_id'],
                entity_name=sample_data['entity_name'],
                entity_type=sample_data['entity_type'],
                expected_normalized_id=sample_data['expected_normalized_id'],
                expected_normalized_name=sample_data['expected_normalized_name'],
                is_correct=sample_data.get('is_correct'),
                confidence=sample_data.get('confidence'),
                notes=sample_data.get('notes')
            )
            self.validation_samples.append(sample)
            
        # Load relationship samples
        self.relationship_validation_samples = []
        for sample_data in data.get('relationship_samples', []):
            sample = RelationshipValidationSample(
                subject_id=sample_data['subject_id'],
                predicate=sample_data['predicate'],
                object_id=sample_data['object_id'],
                is_correct=sample_data.get('is_correct'),
                confidence=sample_data.get('confidence'),
                notes=sample_data.get('notes')
            )
            self.relationship_validation_samples.append(sample)
            
        logger.info(f"Loaded validation samples from {filepath}")

    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive validation report
        
        Returns:
            Dictionary with validation report
        """
        summary = self.get_validation_summary()
        
        # Entity type breakdown
        type_breakdown = defaultdict(int)
        for sample in self.validation_samples:
            type_breakdown[sample.entity_type] += 1
            
        # Confidence distribution
        confidence_bins = defaultdict(int)
        for sample in self.validation_samples:
            if sample.confidence is not None:
                bin_key = int(sample.confidence * 10) / 10  # Round to 0.1
                confidence_bins[bin_key] += 1
                
        return {
            'summary': summary,
            'entity_type_distribution': dict(type_breakdown),
            'confidence_distribution': dict(confidence_bins),
            'validation_threshold': self.validation_threshold,
            'overall_status': 'PASS' if summary['entity_validation']['precision'] >= self.validation_threshold else 'FAIL'
        }

    def auto_validate_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform automatic validation of entities using heuristic rules
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Dictionary with validation results
        """
        validation_results = []
        
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            entity_name = entity.get('entity_name', '').lower()
            normalized_id = entity.get('normalized_id', '')
            normalized_name = entity.get('normalized_name', '').lower()
            confidence = entity.get('confidence_score', 0.0)
            
            # Heuristic validation rules
            is_correct = True
            notes = []
            
            # Check if normalized ID follows expected format
            if normalized_id:
                if entity.get('entity_type') == 'organism' and not normalized_id.startswith('NCBITaxon:'):
                    is_correct = False
                    notes.append("Organism normalized ID should start with NCBITaxon:")
                elif entity.get('entity_type') == 'phenotype' and not (normalized_id.startswith('GO:') or 'GO:' in normalized_id):
                    is_correct = False
                    notes.append("Phenotype normalized ID should be a GO term")
                    
            # Check confidence threshold
            if confidence < 0.5:
                is_correct = False
                notes.append("Low confidence score")
                
            # Check name consistency
            if normalized_name and entity_name and normalized_name not in entity_name and entity_name not in normalized_name:
                # Allow some flexibility for name variations
                if not (entity_name.replace(' ', '') in normalized_name.replace(' ', '') or 
                        normalized_name.replace(' ', '') in entity_name.replace(' ', '')):
                    notes.append("Entity name and normalized name mismatch")
                    
            validation_results.append((entity_id, is_correct, '; '.join(notes) if notes else None))
            
        return self.validate_entity_samples(validation_results)

    def auto_validate_relationships(self, relationships: List[Dict[str, Any]], 
                                  entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform automatic validation of relationships using heuristic rules
        
        Args:
            relationships: List of relationship dictionaries
            entities: List of entity dictionaries for context
            
        Returns:
            Dictionary with validation results
        """
        # Create entity lookup
        entity_lookup = {e.get('entity_id', ''): e for e in entities}
        
        validation_results = []
        
        for rel in relationships:
            subject_id = rel.get('subject_id', '')
            predicate = rel.get('predicate', '')
            object_id = rel.get('object_id', '')
            confidence = rel.get('confidence_score', 0.0)
            
            # Heuristic validation rules
            is_correct = True
            notes = []
            
            # Check if entities exist
            if subject_id not in entity_lookup:
                is_correct = False
                notes.append("Subject entity not found")
                
            if object_id not in entity_lookup:
                is_correct = False
                notes.append("Object entity not found")
                
            # Check entity type compatibility
            if subject_id in entity_lookup and object_id in entity_lookup:
                subject_entity = entity_lookup[subject_id]
                object_entity = entity_lookup[object_id]
                
                # Basic type compatibility rules
                if predicate == 'shows' and subject_entity.get('entity_type') != 'organism':
                    notes.append("Subject of 'shows' relationship should be an organism")
                    
                if predicate == 'measures' and subject_entity.get('entity_type') not in ['assay', 'platform']:
                    notes.append("Subject of 'measures' relationship should be an assay or platform")
                    
            # Check confidence threshold
            if confidence < 0.3:
                is_correct = False
                notes.append("Low confidence score")
                
            validation_results.append((subject_id, predicate, object_id, is_correct, '; '.join(notes) if notes else None))
            
        return self.validate_relationship_samples(validation_results)

def main():
    """
    Main function to demonstrate KG validator functionality
    """
    # Initialize validator
    validator = KGValidator(validation_threshold=0.8)
    
    # Example entities
    example_entities = [
        {
            'entity_id': 'ent_1',
            'entity_name': 'Arabidopsis thaliana',
            'entity_type': 'organism',
            'normalized_id': 'NCBITaxon:3702',
            'normalized_name': 'Arabidopsis thaliana',
            'confidence_score': 0.95
        },
        {
            'entity_id': 'ent_2',
            'entity_name': 'root growth',
            'entity_type': 'phenotype',
            'normalized_id': 'GO:0048468',
            'normalized_name': 'cell development',
            'confidence_score': 0.85
        },
        {
            'entity_id': 'ent_3',
            'entity_name': 'microscopy',
            'entity_type': 'platform',
            'normalized_id': 'OBI:0000245',
            'normalized_name': 'microscopy',
            'confidence_score': 0.90
        }
    ]
    
    # Example relationships
    example_relationships = [
        {
            'subject_id': 'ent_1',
            'predicate': 'shows',
            'object_id': 'ent_2',
            'confidence_score': 0.88
        },
        {
            'subject_id': 'ent_3',
            'predicate': 'used_for',
            'object_id': 'ent_2',
            'confidence_score': 0.75
        }
    ]
    
    print("Example entities:")
    for entity in example_entities:
        print(f"  {entity['entity_type']}: {entity['entity_name']} -> {entity.get('normalized_name', 'Not normalized')}")
    
    print("\nExample relationships:")
    for rel in example_relationships:
        print(f"  {rel['subject_id']} --{rel['predicate']}--> {rel['object_id']} (confidence: {rel['confidence_score']})")
    
    # Create validation samples
    entity_samples = validator.create_entity_validation_samples(example_entities, sample_size=3)
    rel_samples = validator.create_relationship_validation_samples(example_relationships, sample_size=2)
    
    print(f"\nCreated {len(entity_samples)} entity validation samples")
    print(f"Created {len(rel_samples)} relationship validation samples")
    
    # Perform automatic validation
    entity_validation = validator.auto_validate_entities(example_entities)
    print(f"\nEntity validation results: {entity_validation}")
    
    rel_validation = validator.auto_validate_relationships(example_relationships, example_entities)
    print(f"Relationship validation results: {rel_validation}")
    
    # Generate comprehensive report
    report = validator.generate_validation_report()
    print(f"\nValidation report: {report}")

if __name__ == "__main__":
    main()