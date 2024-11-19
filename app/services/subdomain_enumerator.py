# app/services/subdomain_enumerator.py

import asyncio
from typing import List
import logging

logger = logging.getLogger("bbrf")

class SubdomainEnumerator:
    @staticmethod
    async def enumerate(domain: str) -> List[str]:
        try:
            logger.info(f"Starting subdomain enumeration for {domain}")
            process = await asyncio.create_subprocess_exec(
                'subfinder', '-d', domain, '-silent',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Subfinder failed for {domain}: {stderr.decode()}")
                return []
            
            subdomains = stdout.decode().strip().split('\n')
            valid_subdomains = [subdomain for subdomain in subdomains if subdomain]
            logger.info(f"Found {len(valid_subdomains)} subdomains for {domain}")
            return valid_subdomains
        except Exception as e:
            logger.exception(f"Unexpected error during subdomain enumeration for {domain}: {str(e)}")
            return []