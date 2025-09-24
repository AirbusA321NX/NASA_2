import requests
import logging
import time
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GROBIDProcessor:
    """
    Deterministic extraction pipeline using GROBID service for TEI/XML processing
    """
    
    def __init__(self, grobid_url: str = "http://localhost:8070"):
        self.grobid_url = grobid_url
        self.api_url = urljoin(grobid_url, "/api/processFulltextDocument")
        self.health_url = urljoin(grobid_url, "/api/isalive")
        
    def is_service_available(self) -> bool:
        """
        Check if GROBID service is available
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            response = requests.get(self.health_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"GROBID service not available: {e}")
            return False

    def process_pdf_content(self, pdf_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Process PDF content through GROBID to extract TEI/XML with section boundaries
        
        Args:
            pdf_content: PDF content as bytes
            
        Returns:
            Dictionary with extracted document structure or None if failed
        """
        if not self.is_service_available():
            logger.error("GROBID service is not available")
            return None
            
        try:
            # Send PDF to GROBID for processing
            files = {'input': ('document.pdf', pdf_content, 'application/pdf')}
            response = requests.post(
                self.api_url,
                files=files,
                timeout=120  # 2 minute timeout for processing
            )
            
            if response.status_code == 200:
                # Parse TEI/XML response
                tei_xml = response.text
                return self._parse_tei_xml(tei_xml)
            else:
                logger.error(f"GROBID processing failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error processing PDF with GROBID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GROBID processing: {e}")
            return None

    def process_pdf_file(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Process PDF file through GROBID
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted document structure or None if failed
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            return self.process_pdf_content(pdf_content)
        except Exception as e:
            logger.error(f"Error reading PDF file {pdf_path}: {e}")
            return None

    def process_pdf_url(self, pdf_url: str) -> Optional[Dict[str, Any]]:
        """
        Download PDF from URL and process through GROBID
        
        Args:
            pdf_url: URL to PDF file
            
        Returns:
            Dictionary with extracted document structure or None if failed
        """
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            if 'application/pdf' not in response.headers.get('content-type', ''):
                logger.warning(f"Content at {pdf_url} may not be a PDF")
            
            return self.process_pdf_content(response.content)
        except requests.RequestException as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None

    def _parse_tei_xml(self, tei_xml: str) -> Dict[str, Any]:
        """
        Parse TEI/XML from GROBID to extract document structure
        
        Args:
            tei_xml: TEI/XML string from GROBID
            
        Returns:
            Dictionary with structured document content
        """
        try:
            # Parse XML
            root = ET.fromstring(tei_xml)
            
            # Extract document metadata
            metadata = self._extract_metadata(root)
            
            # Extract sections
            sections = self._extract_sections(root)
            
            # Extract bibliography
            bibliography = self._extract_bibliography(root)
            
            return {
                'metadata': metadata,
                'sections': sections,
                'bibliography': bibliography,
                'raw_tei': tei_xml
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parsing TEI/XML: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting document structure: {e}")
            return None

    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """
        Extract document metadata from TEI XML
        
        Args:
            root: Root element of TEI XML
            
        Returns:
            Dictionary with document metadata
        """
        metadata = {}
        
        # Extract title
        title_elem = root.find('.//titleStmt/title')
        if title_elem is not None:
            metadata['title'] = title_elem.text
            
        # Extract authors
        authors = []
        author_elems = root.findall('.//sourceDesc/biblStruct/analytic/author')
        for author_elem in author_elems:
            author = {}
            pers_name = author_elem.find('persName')
            if pers_name is not None:
                forename = pers_name.find('forename')
                surname = pers_name.find('surname')
                if forename is not None and surname is not None:
                    author['name'] = f"{forename.text} {surname.text}"
                elif surname is not None:
                    author['name'] = surname.text
                    
            # Extract affiliation
            affiliation = author_elem.find('affiliation')
            if affiliation is not None:
                org_name = affiliation.find('orgName')
                if org_name is not None:
                    author['affiliation'] = org_name.text
                    
            if author:
                authors.append(author)
                
        metadata['authors'] = authors
        
        # Extract publication info
        publication_stmt = root.find('.//sourceDesc/biblStruct/monogr/imprint')
        if publication_stmt is not None:
            date_elem = publication_stmt.find('date')
            if date_elem is not None:
                metadata['publication_date'] = date_elem.get('when', '')
                
            publisher_elem = publication_stmt.find('publisher')
            if publisher_elem is not None:
                metadata['publisher'] = publisher_elem.text
        
        return metadata

    def _extract_sections(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract document sections from TEI XML
        
        Args:
            root: Root element of TEI XML
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Define section types to extract
        section_mapping = {
            'title': './/titleStmt/title',
            'abstract': './/abstract',
            'introduction': './/div[@type="introduction"]',
            'methods': './/div[@type="methods"]',
            'results': './/div[@type="results"]',
            'conclusions': './/div[@type="conclusions"]',
            'discussion': './/div[@type="discussion"]'
        }
        
        # Extract each section type
        for section_type, xpath in section_mapping.items():
            section_elem = root.find(xpath)
            if section_elem is not None:
                # Extract text content
                content = self._extract_text_content(section_elem)
                if content.strip():
                    sections.append({
                        'type': section_type,
                        'content': content.strip(),
                        'byte_start': 0,  # Would need to calculate actual positions
                        'byte_end': len(content.strip()),
                        'token_start': 0,  # Would need to calculate actual positions
                        'token_end': len(content.strip().split())
                    })
        
        # Extract all div sections if specific ones not found
        if not sections:
            div_elements = root.findall('.//body/div')
            for i, div_elem in enumerate(div_elements):
                content = self._extract_text_content(div_elem)
                if content.strip():
                    # Try to determine section type from head element
                    head_elem = div_elem.find('head')
                    section_type = head_elem.text.lower() if head_elem is not None and head_elem.text else f"section_{i+1}"
                    
                    sections.append({
                        'type': section_type,
                        'content': content.strip(),
                        'byte_start': 0,
                        'byte_end': len(content.strip()),
                        'token_start': 0,
                        'token_end': len(content.strip().split())
                    })
        
        return sections

    def _extract_text_content(self, element: ET.Element) -> str:
        """
        Extract all text content from an XML element, preserving structure
        
        Args:
            element: XML element to extract text from
            
        Returns:
            Extracted text content
        """
        # Handle different element types
        if element.tag in ['p', 'head']:
            # Paragraph or heading
            return ''.join(element.itertext()).strip()
        elif element.tag == 'div':
            # Division - extract all paragraph content
            paragraphs = element.findall('.//p')
            content = '\n\n'.join(self._extract_text_content(p) for p in paragraphs)
            return content
        elif element.tag == 'abstract':
            # Abstract - extract content
            return ''.join(element.itertext()).strip()
        else:
            # Generic extraction
            return ''.join(element.itertext()).strip()

    def _extract_bibliography(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract bibliography from TEI XML
        
        Args:
            root: Root element of TEI XML
            
        Returns:
            List of bibliography entries
        """
        bibliography = []
        
        # Extract references
        ref_elements = root.findall('.//listBibl/biblStruct')
        for ref_elem in ref_elements:
            entry = {}
            
            # Extract title
            title_elem = ref_elem.find('.//analytic/title')
            if title_elem is not None:
                entry['title'] = title_elem.text
                
            # Extract authors
            authors = []
            author_elems = ref_elem.findall('.//analytic/author')
            for author_elem in author_elems:
                pers_name = author_elem.find('persName')
                if pers_name is not None:
                    forename = pers_name.find('forename')
                    surname = pers_name.find('surname')
                    if forename is not None and surname is not None:
                        authors.append(f"{forename.text} {surname.text}")
                    elif surname is not None:
                        authors.append(surname.text)
            entry['authors'] = authors
            
            # Extract publication info
            imprint = ref_elem.find('.//monogr/imprint')
            if imprint is not None:
                # Extract date
                date_elem = imprint.find('date')
                if date_elem is not None:
                    entry['year'] = date_elem.get('when', '')
                    
                # Extract journal/publisher
                publisher_elem = imprint.find('publisher')
                if publisher_elem is not None:
                    entry['publisher'] = publisher_elem.text
                    
                # Extract bibliographic scope (volume, issue, pages)
                for scope_elem in imprint.findall('biblScope'):
                    scope_type = scope_elem.get('unit', '')
                    if scope_type:
                        entry[scope_type] = scope_elem.text
            
            # Extract DOI
            idno_elem = ref_elem.find('.//idno[@type="DOI"]')
            if idno_elem is not None:
                entry['doi'] = idno_elem.text
                
            bibliography.append(entry)
            
        return bibliography

    def batch_process_pdfs(self, pdf_sources: List[str], 
                          source_type: str = "file") -> List[Dict[str, Any]]:
        """
        Batch process multiple PDFs
        
        Args:
            pdf_sources: List of PDF file paths or URLs
            source_type: "file" or "url"
            
        Returns:
            List of processing results
        """
        results = []
        
        for i, source in enumerate(pdf_sources):
            logger.info(f"Processing PDF {i+1}/{len(pdf_sources)}: {source}")
            
            try:
                if source_type == "file":
                    result = self.process_pdf_file(source)
                elif source_type == "url":
                    result = self.process_pdf_url(source)
                else:
                    logger.error(f"Unknown source type: {source_type}")
                    result = None
                    
                results.append({
                    'source': source,
                    'result': result,
                    'success': result is not None
                })
                
                # Add delay to avoid overwhelming the service
                if i < len(pdf_sources) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing {source}: {e}")
                results.append({
                    'source': source,
                    'result': None,
                    'success': False,
                    'error': str(e)
                })
        
        return results

def main():
    """
    Main function to demonstrate GROBID processor functionality
    """
    # Initialize GROBID processor
    processor = GROBIDProcessor(grobid_url=os.getenv("GROBID_URL", "http://localhost:8070"))
    
    # Check if service is available
    if not processor.is_service_available():
        print("GROBID service is not available. Please start the GROBID service.")
        return
    
    # Create a simple test PDF content (in real usage, this would be actual PDF bytes)
    # For demonstration, we'll show the structure without actual processing
    print("GROBID processor initialized successfully")
    print("Ready to process PDFs through GROBID service")

if __name__ == "__main__":
    main()