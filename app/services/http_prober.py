# app/services/http_prober.py

import asyncio
import json
import logging
import shutil
from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.operations import get_dns_resolutions_for_probing, add_http_probe_results

logger = logging.getLogger("bbrf")

class HTTPProber:
    @staticmethod
    async def probe(domains: List[str]) -> List[Dict]:
        if not shutil.which('httpx'):
            logger.error("httpx is not installed or not in PATH")
            return []

        logger.info(f"Starting HTTP probing for {len(domains)} domains")
        results = []

        for domain in domains:
            try:
                logger.debug(f"Probing domain: {domain}")
                process = await asyncio.create_subprocess_exec(
                    'httpx', '-silent', '-status-code', '-title', '-content-length', '-tech-detect', '-json',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate(domain.encode())
                
                if process.returncode != 0:
                    logger.error(f"httpx failed for {domain}: {stderr.decode()}")
                    continue
                
                try:
                    result = json.loads(stdout.decode().strip())
                    results.append(result)
                    logger.info(f"Probed {domain}: {result.get('status_code')} {result.get('title')}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for {domain}")
            
            except Exception as e:
                logger.exception(f"Error probing {domain}: {str(e)}")

        logger.info(f"HTTP probing completed. Probed {len(results)} out of {len(domains)} domains")
        return results

    @staticmethod
    def get_domains_for_probing(domain: str) -> List[str]:
        db = SessionLocal()
        try:
            resolutions = get_dns_resolutions_for_probing(db, domain)
            domains = [resolution.resolved_domain for resolution in resolutions]
            logger.info(f"Retrieved {len(domains)} domains for HTTP probing")
            return domains
        except Exception as e:
            logger.exception(f"Error retrieving domains for probing: {str(e)}")
            return []
        finally:
            db.close()

    @staticmethod
    async def probe_domain(domain: str) -> List[Dict]:
        domains = HTTPProber.get_domains_for_probing(domain)
        if not domains:
            logger.warning(f"No domains found for HTTP probing for {domain}")
            return []
        
        probe_results = await HTTPProber.probe(domains)
        
        db = SessionLocal()
        try:
            added_count = add_http_probe_results(db, domain, probe_results)
            logger.info(f"Added/updated {added_count} HTTP probe results in the database")
        finally:
            db.close()
        
        return probe_results