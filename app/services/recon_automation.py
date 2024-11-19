from app.services.subdomain_enumerator import SubdomainEnumerator
from app.services.dns_resolver import DNSResolver
from app.services.http_prober import HTTPProber
from app.db.database import SessionLocal
from app.db.operations import add_subdomains, add_dns_resolutions, add_http_probe_results, get_subdomains
import logging
from datetime import datetime

logger = logging.getLogger("bbrf")

class ReconAutomation:
    @staticmethod
    async def basic_recon(domain: str):
        logger.info(f"Starting basic recon for domain: {domain}")
        db = SessionLocal()
        start_time = datetime.now()
        
        try:
            # Step 1: Subdomain Enumeration
            subdomains = await SubdomainEnumerator.enumerate(domain)
            added_subdomains = add_subdomains(domain, subdomains)
            logger.info(f"Enumerated and added {added_subdomains} subdomains for {domain}")

            # Step 2: DNS Resolution
            all_subdomains = get_subdomains(domain)
            subdomain_list = [subdomain.subdomain for subdomain in all_subdomains]
            dns_results = await DNSResolver.resolve(subdomain_list)
            
            total_dns_added = 0
            for subdomain in all_subdomains:
                subdomain_resolutions = [d for d in dns_results if d['host'] == subdomain.subdomain]
                if subdomain_resolutions:
                    added_count = add_dns_resolutions(subdomain.id, subdomain_resolutions)
                    total_dns_added += added_count
            
            logger.info(f"Resolved and added DNS for {total_dns_added} subdomains of {domain}")

            # Step 3: HTTP Probing
            http_results = await HTTPProber.probe_domain(domain)
            added_http_results = add_http_probe_results(db, domain, http_results)
            logger.info(f"Completed HTTP probing and added {added_http_results} results for {domain}")

            db.commit()
            
            end_time = datetime.now()
            total_time = end_time - start_time

            return {
                "subdomains_added": added_subdomains,
                "dns_results_added": total_dns_added,
                "http_results_added": added_http_results,
                "total_time": str(total_time)
            }
        
        except Exception as e:
            logger.error(f"Error during basic recon for {domain}: {str(e)}")
            db.rollback()
            raise
        
        finally:
            db.close()