# app/db/operations.py

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.sql import func
from typing import List, Dict
from .models import Subdomain, DNSResolution, HTTPProbeResult
from .database import SessionLocal
import logging

logger = logging.getLogger("bbrf")

# Existing functions

def add_subdomains(domain: str, subdomains: list[str]):
    db = SessionLocal()
    try:
        stmt = insert(Subdomain).values([
            {"domain": domain, "subdomain": subdomain} for subdomain in subdomains
        ])
        
        do_update_stmt = stmt.on_conflict_do_update(
            index_elements=['domain', 'subdomain'],
            set_=dict(updated_at=stmt.excluded.updated_at)
        )
        
        result = db.execute(do_update_stmt)
        db.commit()
        logger.info(f"Added/updated {result.rowcount} subdomains for domain {domain}")
        return result.rowcount
    except IntegrityError as e:
        logger.error(f"IntegrityError while adding subdomains for {domain}: {str(e)}")
        db.rollback()
        return 0
    except Exception as e:
        logger.error(f"Error adding subdomains for {domain}: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

def get_subdomains(domain: str):
    db = SessionLocal()
    try:
        subdomains = db.query(Subdomain).filter(Subdomain.domain == domain).all()
        logger.info(f"Retrieved {len(subdomains)} subdomains for domain {domain}")
        return subdomains
    except Exception as e:
        logger.error(f"Error retrieving subdomains for {domain}: {str(e)}")
        return []
    finally:
        db.close()

# New functions for DNS resolution

def add_dns_resolutions(subdomain_id: int, resolutions: List[Dict]):
    db = SessionLocal()
    try:
        logger.info(f"Adding DNS resolutions for subdomain ID {subdomain_id}")
        logger.debug(f"Resolutions to add: {resolutions}")
        
        added_count = 0
        for resolution in resolutions:
            stmt = insert(DNSResolution).values(
                subdomain_id=subdomain_id,
                resolved_domain=resolution['host'],
                ip_address=resolution['a'][0] if resolution.get('a') else None,
                ttl=resolution.get('ttl'),
                raw_data=resolution
            )
            
            do_update_stmt = stmt.on_conflict_do_update(
                index_elements=['subdomain_id', 'resolved_domain'],
                set_=dict(
                    ip_address=stmt.excluded.ip_address,
                    ttl=stmt.excluded.ttl,
                    raw_data=stmt.excluded.raw_data,
                    created_at=func.now()
                )
            )
            
            result = db.execute(do_update_stmt)
            added_count += result.rowcount

        db.commit()
        logger.info(f"Added/updated {added_count} DNS resolutions for subdomain ID {subdomain_id}")
        return added_count
    except Exception as e:
        logger.error(f"Error adding DNS resolutions for subdomain ID {subdomain_id}: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

def get_dns_resolutions(domain: str):
    db = SessionLocal()
    try:
        resolutions = (
            db.query(DNSResolution)
            .options(joinedload(DNSResolution.subdomain))
            .join(Subdomain)
            .filter(Subdomain.domain == domain)
            .all()
        )
        logger.info(f"Retrieved {len(resolutions)} DNS resolutions for domain {domain}")
        if not resolutions:
            logger.warning(f"No DNS resolutions found in the database for domain {domain}")
        
        # Explicitly access the subdomain to ensure it's loaded
        for resolution in resolutions:
            _ = resolution.subdomain.subdomain

        return resolutions
    except Exception as e:
        logger.error(f"Error retrieving DNS resolutions for {domain}: {str(e)}")
        return []
    finally:
        db.close()

def get_subdomains_with_resolutions(domain: str):
    db = SessionLocal()
    try:
        subdomains = db.query(Subdomain).filter(Subdomain.domain == domain).options(joinedload(Subdomain.dns_resolutions)).all()
        logger.info(f"Retrieved {len(subdomains)} subdomains with DNS resolutions for domain {domain}")
        return subdomains
    except Exception as e:
        logger.error(f"Error retrieving subdomains with DNS resolutions for {domain}: {str(e)}")
        return []
    finally:
        db.close()

# Operations for HTTP Module 

def get_dns_resolutions_for_probing(db: Session, domain: str) -> List[DNSResolution]:
    try:
        logger.info(f"Retrieving DNS resolutions for HTTP probing for domain: {domain}")
        
        # Query to get the latest DNS resolution for each subdomain
        latest_resolutions = db.query(
            DNSResolution.subdomain_id,
            func.max(DNSResolution.created_at).label('latest_created_at')
        ).group_by(DNSResolution.subdomain_id).subquery()

        # Join with the main DNSResolution table to get the full resolution data
        resolutions = db.query(DNSResolution).join(
            latest_resolutions,
            (DNSResolution.subdomain_id == latest_resolutions.c.subdomain_id) &
            (DNSResolution.created_at == latest_resolutions.c.latest_created_at)
        ).join(Subdomain).filter(Subdomain.domain == domain).all()

        logger.info(f"Retrieved {len(resolutions)} DNS resolutions for HTTP probing")
        return resolutions
    except Exception as e:
        logger.exception(f"Error retrieving DNS resolutions for HTTP probing: {str(e)}")
        return []
    
def add_http_probe_results(db: Session, domain: str, probe_results: List[Dict]):
    try:
        logger.info(f"Adding HTTP probe results for domain: {domain}")
        added_count = 0
        
        for result in probe_results:
            subdomain = db.query(Subdomain).filter(Subdomain.domain == domain, Subdomain.subdomain == result['input']).first()
            if not subdomain:
                logger.warning(f"Subdomain not found for {result['input']}. Skipping.")
                continue

            stmt = insert(HTTPProbeResult).values(
                subdomain_id=subdomain.id,
                url=result['url'],
                status_code=result.get('status_code'),
                title=result.get('title'),
                content_length=result.get('content_length'),
                technologies=result.get('tech'),
                webserver=result.get('webserver'),
                ip_address=result.get('host'),
                response_time=result.get('time'),
                raw_data=result
            )

            do_update_stmt = stmt.on_conflict_do_update(
                index_elements=['subdomain_id', 'url'],
                set_=dict(
                    status_code=stmt.excluded.status_code,
                    title=stmt.excluded.title,
                    content_length=stmt.excluded.content_length,
                    technologies=stmt.excluded.technologies,
                    webserver=stmt.excluded.webserver,
                    ip_address=stmt.excluded.ip_address,
                    response_time=stmt.excluded.response_time,
                    raw_data=stmt.excluded.raw_data,
                    created_at=func.now()
                )
            )

            result = db.execute(do_update_stmt)
            added_count += result.rowcount

        db.commit()
        logger.info(f"Added/updated {added_count} HTTP probe results for domain {domain}")
        return added_count
    except IntegrityError as e:
        logger.error(f"IntegrityError while adding HTTP probe results for {domain}: {str(e)}")
        db.rollback()
        return 0
    except Exception as e:
        logger.error(f"Error adding HTTP probe results for {domain}: {str(e)}")
        db.rollback()
        return 0
    
def get_http_probe_results(db: Session, domain: str):
    try:
        logger.info(f"Retrieving HTTP probe results for domain: {domain}")
        results = (
            db.query(HTTPProbeResult, DNSResolution.ip_address)
            .join(Subdomain, HTTPProbeResult.subdomain_id == Subdomain.id)
            .outerjoin(
                DNSResolution,
                (DNSResolution.subdomain_id == Subdomain.id) &
                (DNSResolution.resolved_domain == func.split_part(HTTPProbeResult.url, '://', 2))
            )
            .filter(Subdomain.domain == domain)
            .all()
        )
        logger.info(f"Retrieved {len(results)} HTTP probe results for {domain}")
        return results
    except Exception as e:
        logger.error(f"Error retrieving HTTP probe results for {domain}: {str(e)}")
        return []
    
# Operations for the screenshot module
def get_urls_for_domain(db: Session, domain: str) -> List[str]:
    try:
        logger.info(f"Retrieving URLs for domain: {domain}")
        
        urls = db.query(HTTPProbeResult.url)\
            .join(Subdomain, HTTPProbeResult.subdomain_id == Subdomain.id)\
            .filter(Subdomain.domain == domain)\
            .distinct(HTTPProbeResult.subdomain_id, HTTPProbeResult.url)\
            .all()
        
        # Extract URLs from the result tuples
        url_list = [url[0] for url in urls]
        
        logger.info(f"Retrieved {len(url_list)} unique URLs for domain {domain}")
        return url_list
    except Exception as e:
        logger.error(f"Error retrieving URLs for domain {domain}: {str(e)}")
        return []