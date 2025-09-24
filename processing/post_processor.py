import re
import logging
from typing import Dict, List, Any, Optional
import spacy
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentPostProcessor:
    """
    Post-processing rules to normalize section names and strip references/figures
    """
    
    def __init__(self):
        # Load spaCy model for NLP processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None
            
        # Define section name mappings for normalization
        self.section_mappings = {
            # Title variations for common sections
            'introduction': ['introduction', 'intro', 'background', 'motivation', 'rationale'],
            'methods': ['methods', 'methodology', 'experimental', 'experimental design', 'materials and methods', 'materials & methods'],
            'results': ['results', 'findings', 'outcomes', 'data', 'analysis'],
            'discussion': ['discussion', 'interpretation', 'implications'],
            'conclusions': ['conclusions', 'conclusion', 'summary', 'final remarks'],
            'abstract': ['abstract', 'summary'],
            'references': ['references', 'bibliography', 'works cited'],
            'acknowledgements': ['acknowledgements', 'acknowledgments', 'acknowledgement', 'acknowledgment']
        }
        
        # Compile regex patterns for reference removal
        self.reference_patterns = [
            # Citation patterns
            r'\(\s*\d{4}\s*\)',  # (2023)
            r'\(\s*\d{2,4}\s*[a-zA-Z]?\s*\)',  # (23) or (2023a)
            r'\[\s*\d+\s*\]',  # [1]
            r'\[\s*\d+\s*[–\-]\s*\d+\s*\]',  # [1-5]
            r'\d+\s*\(\s*\d{4}\s*\)',  # 1 (2023)
            r'et\s+al\.',  # et al.
            # DOI patterns
            r'https?://[^\s]+doi[^\s]*',
            r'doi:\s*[^\s]+',
            # Figure/table references
            r'figure\s+\d+[a-z]?',  # Figure 1, Figure 2a
            r'fig\.\s*\d+[a-z]?',  # Fig. 1, Fig. 2a
            r'table\s+\d+[a-z]?',  # Table 1, Table 2a
            r'\(?\s*see\s+figure\s+\d+\s*\)?',  # (see Figure 1)
            r'\(?\s*see\s+table\s+\d+\s*\)?',  # (see Table 1)
        ]
        
        # Compile regex patterns for figure/table caption removal
        self.figure_table_patterns = [
            r'figure\s+\d+[a-z]?\s*:.*?(?=\n\n|\Z)',  # Figure 1: Caption...
            r'fig\.\s*\d+[a-z]?\s*:.*?(?=\n\n|\Z)',  # Fig. 1: Caption...
            r'table\s+\d+[a-z]?\s*:.*?(?=\n\n|\Z)',  # Table 1: Caption...
            r'^figure\s+\d+[a-z]?.*?(?=\n\n|\Z)',  # Figure 1 at start of line
            r'^table\s+\d+[a-z]?.*?(?=\n\n|\Z)',  # Table 1 at start of line
        ]

    def normalize_section_names(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize section names to standard types
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            List of sections with normalized names
        """
        normalized_sections = []
        
        for section in sections:
            original_type = section.get('type', '').lower()
            normalized_type = self._normalize_section_name(original_type)
            
            normalized_section = section.copy()
            normalized_section['original_type'] = original_type
            normalized_section['type'] = normalized_type
            
            normalized_sections.append(normalized_section)
            
        return normalized_sections

    def _normalize_section_name(self, section_name: str) -> str:
        """
        Normalize a single section name
        
        Args:
            section_name: Original section name
            
        Returns:
            Normalized section name
        """
        # Clean the section name
        clean_name = section_name.strip().lower()
        
        # Check each mapping
        for standard_name, variations in self.section_mappings.items():
            if clean_name in variations or any(variation in clean_name for variation in variations):
                return standard_name
                
        # If no match, return original (cleaned)
        return clean_name

    def strip_references(self, text: str) -> str:
        """
        Strip references and citations from text
        
        Args:
            text: Input text
            
        Returns:
            Text with references removed
        """
        # Apply each reference pattern
        for pattern in self.reference_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*,\s*', ', ', text)  # Fix comma spacing
        text = re.sub(r'\s*\.\s*', '. ', text)  # Fix period spacing
        text = re.sub(r'\s*;\s*', '; ', text)  # Fix semicolon spacing
        
        return text.strip()

    def strip_figure_table_captions(self, text: str) -> str:
        """
        Strip figure and table captions from text
        
        Args:
            text: Input text
            
        Returns:
            Text with figure/table captions removed
        """
        # Apply each figure/table pattern
        for pattern in self.figure_table_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
            
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove extra blank lines
        text = text.strip()
        
        return text

    def extract_token_offsets(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract token offsets for text
        
        Args:
            text: Input text
            
        Returns:
            List of token information with offsets
        """
        if not self.nlp:
            # Fallback if spaCy not available
            words = text.split()
            tokens = []
            offset = 0
            for i, word in enumerate(words):
                start = text.find(word, offset)
                end = start + len(word)
                tokens.append({
                    'token': word,
                    'start': start,
                    'end': end,
                    'index': i
                })
                offset = end
            return tokens
            
        # Use spaCy for tokenization
        doc = self.nlp(text)
        tokens = []
        for i, token in enumerate(doc):
            tokens.append({
                'token': token.text,
                'start': token.idx,
                'end': token.idx + len(token.text),
                'index': i,
                'pos': token.pos_,
                'lemma': token.lemma_
            })
        return tokens

    def calculate_byte_offsets(self, text: str) -> Dict[str, int]:
        """
        Calculate byte offsets for text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with start and end byte positions
        """
        return {
            'byte_start': 0,
            'byte_end': len(text.encode('utf-8'))
        }

    def post_process_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply all post-processing rules to sections
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            List of post-processed sections
        """
        processed_sections = []
        
        for section in sections:
            # Create a copy to avoid modifying original
            processed_section = section.copy()
            
            # Get content
            content = processed_section.get('content', '')
            
            # Strip references
            content_no_refs = self.strip_references(content)
            
            # Strip figure/table captions
            content_clean = self.strip_figure_table_captions(content_no_refs)
            
            # Update content
            processed_section['content'] = content_clean
            
            # Recalculate offsets
            byte_offsets = self.calculate_byte_offsets(content_clean)
            processed_section.update(byte_offsets)
            
            # Extract token information
            tokens = self.extract_token_offsets(content_clean)
            processed_section['tokens'] = tokens
            processed_section['token_count'] = len(tokens)
            
            processed_sections.append(processed_section)
            
        return processed_sections

    def identify_section_structure(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify overall document structure from sections
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Dictionary with document structure information
        """
        structure = {
            'section_count': len(sections),
            'section_types': [section['type'] for section in sections],
            'has_title': any(section['type'] == 'title' for section in sections),
            'has_abstract': any(section['type'] == 'abstract' for section in sections),
            'has_introduction': any(section['type'] == 'introduction' for section in sections),
            'has_methods': any(section['type'] == 'methods' for section in sections),
            'has_results': any(section['type'] == 'results' for section in sections),
            'has_conclusions': any(section['type'] == 'conclusions' for section in sections),
            'has_references': any(section['type'] == 'references' for section in sections)
        }
        
        return structure

    def extract_key_terms(self, text: str, max_terms: int = 20) -> List[str]:
        """
        Extract key terms from text using NLP techniques
        
        Args:
            text: Input text
            max_terms: Maximum number of terms to return
            
        Returns:
            List of key terms
        """
        if not self.nlp:
            # Simple fallback
            words = text.lower().split()
            # Filter out common stop words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were'}
            filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
            word_counts = Counter(filtered_words)
            return [word for word, count in word_counts.most_common(max_terms)]
            
        # Use spaCy for advanced term extraction
        doc = self.nlp(text)
        
        # Extract noun phrases and named entities
        terms = []
        
        # Add noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.strip()) > 2:
                terms.append(chunk.text.strip())
                
        # Add named entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART']:
                terms.append(ent.text.strip())
                
        # Add important tokens (nouns, adjectives)
        for token in doc:
            if (token.pos_ in ['NOUN', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text.strip()) > 2):
                terms.append(token.lemma_.strip())
                
        # Count and return most common terms
        term_counts = Counter(terms)
        return [term for term, count in term_counts.most_common(max_terms)]

def main():
    """
    Main function to demonstrate post-processing functionality
    """
    # Initialize post-processor
    processor = DocumentPostProcessor()
    
    # Example sections for demonstration
    example_sections = [
        {
            'type': 'intro',
            'content': 'This is the introduction section with some citations [1] and references (Smith et al., 2023). '
                      'See Figure 1 for details and Table 2 for results.'
        },
        {
            'type': 'methods',
            'content': 'Our methods included several experiments as shown in Figure 3. '
                      'We followed the approach described by Johnson [5] and modified it.'
        },
        {
            'type': 'results',
            'content': 'The results are shown in Table 1 and Figure 4. '
                      'Statistical analysis was performed using standard methods [2, 3].'
        }
    ]
    
    print("Original sections:")
    for section in example_sections:
        print(f"  {section['type']}: {section['content'][:100]}...")
    
    # Normalize section names
    normalized_sections = processor.normalize_section_names(example_sections)
    print("\nSections with normalized names:")
    for section in normalized_sections:
        print(f"  {section['type']} (originally: {section['original_type']})")
    
    # Apply post-processing
    processed_sections = processor.post_process_sections(normalized_sections)
    print("\nPost-processed sections:")
    for section in processed_sections:
        print(f"  {section['type']}: {section['content'][:100]}...")
        print(f"    Tokens: {section['token_count']}")
    
    # Identify document structure
    structure = processor.identify_section_structure(processed_sections)
    print(f"\nDocument structure: {structure}")

if __name__ == "__main__":
    main()