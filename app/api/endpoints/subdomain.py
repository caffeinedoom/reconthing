# app/api/endpoints/subdomain.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
import uuid
import time
import asyncio
from pydantic import Field

from app.schemas.subdomain import SubdomainCreate, SubdomainResponse, TaskResponse, TaskStatus, TaskBase
from app.services.subdomain_enumerator import SubdomainEnumerator
from app.db.operations import add_subdomains, get_subdomains

router = APIRouter()
logger = logging.getLogger("bbrf")

# In-memory task storage. In a production environment, use a proper task queue.
tasks = {}

class TaskStatus(TaskBase):
    status: str
    progress: int = 0
    subdomains: List[str] = []
    error: str = None
    timestamp: float = Field(default_factory=time.time)

@router.post("/enumerate", response_model=TaskResponse)
async def enumerate_subdomains(domain: SubdomainCreate, background_tasks: BackgroundTasks):
    logger.info(f"Starting enumeration for domain: {domain.domain}")
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_enumeration, task_id, domain.domain)
    tasks[task_id] = TaskStatus(task_id=task_id, status="in_progress", progress=0)
    return TaskResponse(task_id=task_id)

async def run_enumeration(task_id: str, domain: str):
    try:
        logger.info(f"Running enumeration for task {task_id}, domain {domain}")
        subdomains = await SubdomainEnumerator.enumerate(domain)
        
        if subdomains:
            added_count = await asyncio.to_thread(add_subdomains, domain, subdomains)
            logger.info(f"Added/updated {added_count} subdomains for {domain}")
            tasks[task_id] = TaskStatus(task_id=task_id, status="completed", progress=100, subdomains=subdomains)
        else:
            logger.warning(f"No subdomains found for {domain}")
            tasks[task_id] = TaskStatus(task_id=task_id, status="completed", progress=100, subdomains=[])
    except Exception as e:
        logger.exception(f"Error enumerating subdomains for {domain}: {str(e)}")
        tasks[task_id] = TaskStatus(task_id=task_id, status="failed", error=str(e))

@router.get("/enumerate/status/{task_id}", response_model=TaskStatus)
async def get_enumeration_status(task_id: str):
    if task_id not in tasks:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@router.get("/subdomains/{domain}", response_model=List[SubdomainResponse])
async def get_domain_subdomains(domain: str):
    logger.info(f"Retrieving subdomains for domain: {domain}")
    subdomains = await asyncio.to_thread(get_subdomains, domain)
    if not subdomains:
        logger.warning(f"No subdomains found for domain: {domain}")
        raise HTTPException(status_code=404, detail="No subdomains found for this domain")
    logger.info(f"Retrieved {len(subdomains)} subdomains for {domain}")
    return subdomains

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