#!/usr/bin/env python3
"""
Test script to list all objects in NASA OSDR bucket
"""

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_s3_full():
    """Test direct S3 access and list all objects"""
    try:
        # Create S3 client with unsigned requests (public bucket)
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        
        logger.info("Listing all objects in NASA OSDR bucket...")
        
        # List objects in the bucket
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket='nasa-osdr', MaxKeys=100)  # Limit to 100 objects for testing
        
        total_objects = 0
        prefixes = set()
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    total_objects += 1
                    key = obj['Key']
                    # Extract prefix (first part of the key)
                    if '/' in key:
                        prefix = key.split('/')[0]
                        prefixes.add(prefix)
                    logger.info(f"Object: {key}")
                    
                    # Stop after showing first few objects
                    if total_objects >= 20:
                        break
            
            if total_objects >= 20:
                break
        
        logger.info(f"Total objects listed: {total_objects}")
        logger.info(f"Unique prefixes found: {sorted(prefixes)}")
            
    except Exception as e:
        logger.error(f"Error accessing NASA OSDR S3 bucket: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    test_s3_full()