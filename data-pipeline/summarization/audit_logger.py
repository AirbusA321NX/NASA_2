import logging
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AuditEntry:
    """Data class for audit log entries"""
    timestamp: str
    entry_type: str  # 'prompt', 'model', 'evidence', 'summary'
    content: Dict[str, Any]
    session_id: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditLogger:
    """
    Audit logging for all LLM prompts, model fingerprints, and evidence snippets
    """
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = log_directory
        self.session_id = self._generate_session_id()
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            
        # Set up audit log file
        self.audit_log_file = os.path.join(
            log_directory, 
            f"audit_log_{self.session_id}.jsonl"
        )
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    def log_prompt(self, 
                   prompt: str, 
                   prompt_type: str,
                   user_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Log an LLM prompt
        
        Args:
            prompt: The prompt text
            prompt_type: Type of prompt (e.g., 'summarization', 'entity_extraction')
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="prompt",
            content={
                "prompt": prompt,
                "prompt_type": prompt_type
            },
            session_id=self.session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        self._write_audit_entry(entry)
        logger.debug(f"Logged prompt: {prompt_type}")
    
    def log_model(self, 
                  model_info: Dict[str, Any],
                  user_id: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Log model information and fingerprints
        
        Args:
            model_info: Dictionary with model information
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="model",
            content=model_info,
            session_id=self.session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        self._write_audit_entry(entry)
        logger.debug(f"Logged model: {model_info.get('model_name', 'unknown')}")
    
    def log_evidence(self, 
                     evidence_snippets: List[Dict[str, Any]],
                     query: str,
                     user_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Log evidence snippets used in summarization
        
        Args:
            evidence_snippets: List of evidence snippet dictionaries
            query: The original query
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="evidence",
            content={
                "query": query,
                "evidence_snippets": evidence_snippets
            },
            session_id=self.session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        self._write_audit_entry(entry)
        logger.debug(f"Logged {len(evidence_snippets)} evidence snippets")
    
    def log_summary(self, 
                    summary_output: Dict[str, Any],
                    user_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None):
        """
        Log summary output
        
        Args:
            summary_output: Summary output dictionary
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="summary",
            content=summary_output,
            session_id=self.session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        self._write_audit_entry(entry)
        logger.debug("Logged summary output")
    
    def _write_audit_entry(self, entry: AuditEntry):
        """
        Write an audit entry to the log file
        
        Args:
            entry: AuditEntry to write
        """
        try:
            # Convert to dictionary and write as JSON line
            entry_dict = asdict(entry)
            
            with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry_dict) + '\n')
                
        except Exception as e:
            logger.error(f"Error writing audit entry: {e}")
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id
    
    def get_audit_log_path(self) -> str:
        """Get the path to the audit log file"""
        return self.audit_log_file
    
    def load_audit_log(self) -> List[Dict[str, Any]]:
        """
        Load all audit entries from the log file
        
        Returns:
            List of audit entry dictionaries
        """
        entries = []
        
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
                            
            return entries
            
        except Exception as e:
            logger.error(f"Error loading audit log: {e}")
            return entries
    
    def export_audit_report(self, report_path: Optional[str] = None) -> str:
        """
        Export a formatted audit report
        
        Args:
            report_path: Optional path for report file
            
        Returns:
            Path to the generated report
        """
        entries = self.load_audit_log()
        
        if not report_path:
            report_path = os.path.join(
                self.log_directory, 
                f"audit_report_{self.session_id}.json"
            )
        
        # Group entries by type
        grouped_entries = {}
        for entry in entries:
            entry_type = entry['entry_type']
            if entry_type not in grouped_entries:
                grouped_entries[entry_type] = []
            grouped_entries[entry_type].append(entry)
        
        # Create report
        report = {
            "session_id": self.session_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_entries": len(entries),
                "entries_by_type": {k: len(v) for k, v in grouped_entries.items()}
            },
            "entries": grouped_entries
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Audit report exported to: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error exporting audit report: {e}")
            raise

def main():
    """
    Main function to demonstrate audit logger functionality
    """
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    print(f"Audit logger initialized with session ID: {audit_logger.get_session_id()}")
    
    # Example audit entries
    audit_logger.log_prompt(
        prompt="Summarize findings about plant growth in microgravity",
        prompt_type="summarization",
        user_id="user_123"
    )
    
    audit_logger.log_model(
        model_info={
            "model_name": "all-mpnet-base-v2",
            "version": "1.0",
            "fingerprint": "abc123def456",
            "type": "embedding"
        },
        user_id="system"
    )
    
    audit_logger.log_evidence(
        evidence_snippets=[
            {
                "paper_id": "paper_001",
                "section_type": "results",
                "content": "Plants grown in microgravity showed 25% reduction in root growth...",
                "score": 0.95,
                "chunk_id": "chunk_789"
            }
        ],
        query="plant growth in microgravity",
        user_id="system"
    )
    
    audit_logger.log_summary(
        summary_output={
            "insight": "Microgravity significantly affects plant root development",
            "evidence_bullets": [
                "[1] Plants grown in microgravity showed 25% reduction in root growth..."
            ],
            "research_gaps": [
                "Further research is needed on the molecular mechanisms underlying these changes"
            ]
        },
        user_id="system"
    )
    
    # Export report
    report_path = audit_logger.export_audit_report()
    print(f"Audit report exported to: {report_path}")
    
    # Show log path
    print(f"Audit log file: {audit_logger.get_audit_log_path()}")

if __name__ == "__main__":
    main()