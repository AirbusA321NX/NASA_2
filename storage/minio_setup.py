import os
import logging
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import aiohttp
import aiofiles
from minio import Minio
from minio.error import S3Error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinIOStorage:
    """
    MinIO object storage for persisting raw PDFs with immutable provenance fields
    """
    
    def __init__(self, 
                 endpoint: str = "localhost:9000",
                 access_key: str = "minioadmin",
                 secret_key: str = "minioadmin",
                 secure: bool = False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = "nasa-pdfs"
        
    async def initialize_storage(self):
        """
        Initialize MinIO storage - create bucket if it doesn't exist
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
                
        except S3Error as e:
            logger.error(f"Error initializing MinIO storage: {e}")
            raise

    def generate_immutable_key(self, content: bytes, source_url: str) -> str:
        """
        Generate an immutable key for storage based on content hash and source
        
        Args:
            content: PDF content bytes
            source_url: Original URL where PDF was fetched
            
        Returns:
            Immutable key for storage
        """
        # Create SHA256 hash of content
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Create SHA256 hash of source URL
        url_hash = hashlib.sha256(source_url.encode()).hexdigest()
        
        # Combine hashes to create unique immutable key
        # This ensures the same content from different sources gets the same key
        # but allows tracking of different sources
        immutable_key = f"pdfs/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.pdf"
        
        return immutable_key

    async def store_pdf(self, 
                       pdf_content: bytes, 
                       source_url: str,
                       metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Store PDF in MinIO with immutable provenance fields
        
        Args:
            pdf_content: PDF content as bytes
            source_url: Original URL where PDF was fetched
            metadata: Additional metadata to store
            
        Returns:
            Dictionary with storage information
        """
        try:
            # Generate immutable key
            immutable_key = self.generate_immutable_key(pdf_content, source_url)
            
            # Prepare metadata with provenance fields
            provenance_metadata = {
                "source-url": source_url,
                "fetch-timestamp": datetime.utcnow().isoformat() + "Z",
                "content-sha256": hashlib.sha256(pdf_content).hexdigest(),
                "content-length": str(len(pdf_content)),
            }
            
            # Add any additional metadata
            if metadata:
                provenance_metadata.update(metadata)
            
            # Store in MinIO
            result = self.client.put_object(
                self.bucket_name,
                immutable_key,
                data=pdf_content,
                length=len(pdf_content),
                metadata=provenance_metadata,
                content_type="application/pdf"
            )
            
            logger.info(f"Stored PDF with key: {immutable_key}")
            
            return {
                "key": immutable_key,
                "bucket": self.bucket_name,
                "etag": result.etag,
                "version_id": result.version_id,
                "source_url": source_url,
                "content_sha256": provenance_metadata["content-sha256"],
                "content_length": int(provenance_metadata["content-length"]),
                "fetch_timestamp": provenance_metadata["fetch-timestamp"]
            }
            
        except S3Error as e:
            logger.error(f"Error storing PDF in MinIO: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error storing PDF: {e}")
            raise

    async def retrieve_pdf(self, key: str) -> bytes:
        """
        Retrieve PDF content from MinIO by key
        
        Args:
            key: Storage key for the PDF
            
        Returns:
            PDF content as bytes
        """
        try:
            response = self.client.get_object(self.bucket_name, key)
            content = response.read()
            response.close()
            response.release_conn()
            return content
            
        except S3Error as e:
            logger.error(f"Error retrieving PDF from MinIO: {e}")
            raise

    async def get_pdf_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for a stored PDF
        
        Args:
            key: Storage key for the PDF
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            stat = self.client.stat_object(self.bucket_name, key)
            
            return {
                "key": key,
                "bucket": self.bucket_name,
                "size": stat.size,
                "etag": stat.etag,
                "version_id": stat.version_id,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "content_type": stat.content_type,
                "metadata": dict(stat.metadata) if stat.metadata else {}
            }
            
        except S3Error as e:
            logger.error(f"Error getting PDF metadata from MinIO: {e}")
            raise

    async def list_pdfs(self, prefix: str = "pdfs/") -> List[Dict[str, Any]]:
        """
        List all PDFs in storage with their metadata
        
        Args:
            prefix: Prefix to filter objects
            
        Returns:
            List of PDF metadata dictionaries
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            
            pdfs = []
            for obj in objects:
                pdf_info = {
                    "key": obj.object_name,
                    "bucket": self.bucket_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None
                }
                pdfs.append(pdf_info)
                
            return pdfs
            
        except S3Error as e:
            logger.error(f"Error listing PDFs in MinIO: {e}")
            raise

    async def download_and_store_pdf(self, 
                                   pdf_url: str,
                                   max_size_mb: int = 100) -> Dict[str, Any]:
        """
        Download PDF from URL and store in MinIO with provenance
        
        Args:
            pdf_url: URL to download PDF from
            max_size_mb: Maximum size limit for PDFs
            
        Returns:
            Dictionary with storage information
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(pdf_url) as response:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if 'application/pdf' not in content_type:
                        logger.warning(f"Content type is not PDF: {content_type}")
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_size_mb * 1024 * 1024:
                        raise ValueError(f"PDF too large: {int(content_length) / (1024*1024):.2f}MB")
                    
                    # Read content
                    pdf_content = await response.read()
                    
                    # Store in MinIO
                    storage_info = await self.store_pdf(
                        pdf_content=pdf_content,
                        source_url=pdf_url,
                        metadata={
                            "original-filename": pdf_url.split('/')[-1],
                            "http-status": str(response.status),
                            "content-type": content_type
                        }
                    )
                    
                    return storage_info
                    
            except aiohttp.ClientError as e:
                logger.error(f"Error downloading PDF from {pdf_url}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error downloading/storing PDF: {e}")
                raise

async def main():
    """
    Main function to demonstrate MinIO storage functionality
    """
    # Initialize MinIO storage
    storage = MinIOStorage(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=False
    )
    
    try:
        # Initialize storage
        await storage.initialize_storage()
        
        # Create a simple test PDF content (in real usage, this would be actual PDF bytes)
        test_pdf_content = b"%PDF-1.4\n%Test PDF content for demonstration\n"
        
        # Store test PDF
        storage_info = await storage.store_pdf(
            pdf_content=test_pdf_content,
            source_url="https://example.com/test.pdf",
            metadata={"test": "metadata"}
        )
        
        print(f"Stored PDF: {storage_info}")
        
        # Retrieve PDF
        retrieved_content = await storage.retrieve_pdf(storage_info["key"])
        print(f"Retrieved PDF content length: {len(retrieved_content)}")
        
        # Get metadata
        metadata = await storage.get_pdf_metadata(storage_info["key"])
        print(f"PDF metadata: {metadata}")
        
        # List PDFs
        pdfs = await storage.list_pdfs()
        print(f"Found {len(pdfs)} PDFs in storage")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())