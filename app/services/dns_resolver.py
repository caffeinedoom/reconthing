# app/services/dns_resolver.py

import asyncio
import json
from typing import List, Dict
import logging
import shutil

logger = logging.getLogger("bbrf")

class DNSResolver:
    @staticmethod
    async def resolve(subdomains: List[str]) -> List[Dict]:
        if not shutil.which('dnsx'):
            logger.error("dnsx is not installed or not in PATH")
            return []

        logger.info(f"Starting DNS resolution for {len(subdomains)} subdomains")
        results = []

        for subdomain in subdomains:
            try:
                logger.debug(f"Processing subdomain: {subdomain}")
                process = await asyncio.create_subprocess_exec(
                    'dnsx', '-a', '-resp', '-json','-silent', 
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate(subdomain.encode())
                
                if process.returncode != 0:
                    logger.error(f"dnsx failed for {subdomain}: {stderr.decode()}")
                    continue
                
                try:
                    result = json.loads(stdout.decode().strip())
                    results.append(result)
                    logger.info(f"Resolved {subdomain}: {result}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for {subdomain}")
            
            except Exception as e:
                logger.exception(f"Error processing {subdomain}: {str(e)}")

        logger.info(f"DNS resolution completed. Resolved {len(results)} out of {len(subdomains)} subdomains")
        return results