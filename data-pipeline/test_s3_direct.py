#!/usr/bin/env python3
"""
Test script to verify direct S3 access to NASA OSDR bucket
"""

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_s3_direct():
    """Test direct S3 access"""
    try:
        # Create S3 client with unsigned requests (public bucket)
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        
        logger.info("Listing objects in NASA OSDR bucket with GLDS prefix...")
        
        # List objects in the bucket with GLDS prefix
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket='nasa-osdr', Prefix='GLDS-', Delimiter='/')
        
        studies = []
        
        for page in pages:
            # Get common prefixes (directories)
            if 'CommonPrefixes' in page:
                for prefix in page['CommonPrefixes']:
                    prefix_name = prefix['Prefix']
                    # Extract study ID from prefix (e.g., "GLDS-123/")
                    if prefix_name.startswith('GLDS-') and prefix_name.endswith('/'):
                        study_id = prefix_name.rstrip('/')
                        logger.info(f"Found GLDS study: {study_id}")
                        studies.append(study_id)
        
        logger.info(f"Found {len(studies)} GLDS studies")
        if studies:
            logger.info("First few studies:")
            for i, study in enumerate(studies[:5]):
                logger.info(f"  {i+1}. {study}")
        else:
            logger.warning("No GLDS studies found")
            
    except Exception as e:
        logger.error(f"Error accessing NASA OSDR S3 bucket: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    test_s3_direct()