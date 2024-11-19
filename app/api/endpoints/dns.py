# app/api/endpoints/dns.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
import uuid
import time
import asyncio

from app.schemas.dns import DNSResolutionCreate, DNSResolutionResponse, TaskResponse, TaskStatus
from app.services.dns_resolver import DNSResolver
from app.db.operations import get_subdomains, add_dns_resolutions, get_dns_resolutions, get_subdomains_with_resolutions

router = APIRouter()
logger = logging.getLogger("bbrf")

# In-memory task storage. In a production environment, use a proper task queue.
tasks = {}

@router.post("/resolve", response_model=TaskResponse)
async def resolve_dns(domain: DNSResolutionCreate, background_tasks: BackgroundTasks):
    logger.info(f"Starting DNS resolution for domain: {domain.domain}")
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_dns_resolution, task_id, domain.domain)
    tasks[task_id] = TaskStatus(task_id=task_id, status="in_progress", progress=0)
    return TaskResponse(task_id=task_id)

async def run_dns_resolution(task_id: str, domain: str):
    try:
        logger.info(f"Running DNS resolution for task {task_id}, domain {domain}")
        subdomains = get_subdomains(domain)
        subdomain_list = [subdomain.subdomain for subdomain in subdomains]
        total_subdomains = len(subdomain_list)
        logger.info(f"Found {total_subdomains} subdomains for {domain}")

        batch_size = 1000  # Process 1000 subdomains at a time
        resolved_domains = []
        total_added = 0

        for i in range(0, total_subdomains, batch_size):
            batch = subdomain_list[i:i+batch_size]
            batch_resolved = await DNSResolver.resolve(batch)
            resolved_domains.extend(batch_resolved)

            for subdomain in subdomains[i:i+batch_size]:
                subdomain_resolutions = [d for d in batch_resolved if d['host'] == subdomain.subdomain]
                if subdomain_resolutions:
                    added_count = add_dns_resolutions(subdomain.id, subdomain_resolutions)
                    total_added += added_count

            progress = min(100, int((i + len(batch)) / total_subdomains * 100))
            tasks[task_id] = TaskStatus(task_id=task_id, status="in_progress", progress=progress, resolutions=resolved_domains)

        logger.info(f"DNS resolution completed. Resolved {len(resolved_domains)} out of {total_subdomains} subdomains")
        logger.info(f"Total DNS resolutions added to database: {total_added}")
        tasks[task_id] = TaskStatus(task_id=task_id, status="completed", progress=100, resolutions=resolved_domains)
    except Exception as e:
        logger.exception(f"Error resolving DNS for {domain}: {str(e)}")
        tasks[task_id] = TaskStatus(task_id=task_id, status="failed", error=str(e))

@router.get("/resolve/status/{task_id}", response_model=TaskStatus)
async def get_resolution_status(task_id: str):
    if task_id not in tasks:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@router.get("/resolutions/{domain}", response_model=List[DNSResolutionResponse])
async def get_domain_resolutions(domain: str):
    logger.info(f"Retrieving DNS resolutions for domain: {domain}")
    resolutions = get_dns_resolutions(domain)
    if not resolutions:
        logger.warning(f"No DNS resolutions found for domain: {domain}")
        raise HTTPException(status_code=404, detail="No DNS resolutions found for this domain")
    logger.info(f"Retrieved {len(resolutions)} DNS resolutions for {domain}")
    return [DNSResolutionResponse(
        subdomain=resolution.subdomain.subdomain,
        resolved_domain=resolution.resolved_domain,
        ip_address=resolution.ip_address,
        ttl=resolution.ttl,
        created_at=resolution.created_at
    ) for resolution in resolutions]

@router.get("/subdomains-with-resolutions/{domain}", response_model=List[DNSResolutionResponse])
async def get_subdomains_with_dns_resolutions(domain: str):
    logger.info(f"Retrieving subdomains with DNS resolutions for domain: {domain}")
    subdomains = get_subdomains_with_resolutions(domain)
    if not subdomains:
        logger.warning(f"No subdomains or DNS resolutions found for domain: {domain}")
        raise HTTPException(status_code=404, detail="No subdomains or DNS resolutions found for this domain")
    
    results = []
    for subdomain in subdomains:
        for resolution in subdomain.dns_resolutions:
            results.append(DNSResolutionResponse(
                subdomain=subdomain.subdomain,
                resolved_domain=resolution.resolved_domain,
                created_at=resolution.created_at
            ))
    
    logger.info(f"Retrieved {len(results)} subdomains with DNS resolutions for {domain}")
    return results

async def cleanup_tasks():
    while True:
        await asyncio.sleep(3600)  # Run every hour
        current_time = time.time()
        tasks_to_remove = [
            task_id for task_id, task in tasks.items()
            if task.status in ["completed", "failed"] and current_time - task.timestamp > 86400  # 24 hours
        ]
        for task_id in tasks_to_remove:
            del tasks[task_id]
        logger.info(f"Cleaned up {len(tasks_to_remove)} completed or failed tasks")

@router.on_event("startup")
async def start_task_cleanup():
    asyncio.create_task(cleanup_tasks())