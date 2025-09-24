#!/usr/bin/env python3
"""
Debug script to see what's in the NASA OSDR repository
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_osdr_fetch():
    """Debug fetching OSDR catalog"""
    base_url = "http://nasa-osdr.s3-website-us-west-2.amazonaws.com"
    
    logger.info(f"Fetching content from: {base_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html_content = await response.text()
                    logger.info(f"Successfully fetched content, length: {len(html_content)} chars")
                    
                    # Save the HTML content to a file for inspection
                    with open("osdr_content.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("Saved HTML content to osdr_content.html")
                    
                    # Parse the HTML content
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Find all links
                    links = soup.find_all('a')
                    logger.info(f"Found {len(links)} links")
                    
                    # Print first few links
                    for i, link in enumerate(links[:10]):
                        href = str(link.get('href', ''))
                        text = str(link.get_text())
                        logger.info(f"  {i+1}. href: '{href}', text: '{text}'")
                    
                    # Look for GLDS patterns
                    glds_pattern = re.compile(r'GLDS-\d+')
                    glds_matches = []
                    
                    for link in links:
                        href = str(link.get('href', ''))
                        text = str(link.get_text())
                        href_match = glds_pattern.search(href)
                        text_match = glds_pattern.search(text)
                        
                        if href_match:
                            glds_matches.append(href_match.group())
                        if text_match:
                            glds_matches.append(text_match.group())
                    
                    logger.info(f"Found {len(glds_matches)} GLDS matches: {glds_matches}")
                    
                else:
                    logger.error(f"Failed to fetch content: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error fetching content: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    asyncio.run(debug_osdr_fetch())