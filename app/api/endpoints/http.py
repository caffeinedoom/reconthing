# app/api/endpoints/http.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
import uuid
import time
import asyncio

from app.schemas.http import HTTPProbeCreate, HTTPProbeResponse, TaskResponse, TaskStatus
from app.services.http_prober import HTTPProber
from app.db.operations import get_http_probe_results
from app.db.database import SessionLocal

router = APIRouter()
logger = logging.getLogger("bbrf")

# In-memory task storage. In a production environment, use a proper task queue.
tasks = {}

@router.post("/probe", response_model=TaskResponse)
async def probe_http(domain: HTTPProbeCreate, background_tasks: BackgroundTasks):
    logger.info(f"Starting HTTP probing for domain: {domain.domain}")
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_http_probe, task_id, domain.domain)
    tasks[task_id] = TaskStatus(task_id=task_id, status="in_progress", progress=0)
    return TaskResponse(task_id=task_id)

async def run_http_probe(task_id: str, domain: str):
    try:
        logger.info(f"Running HTTP probe for task {task_id}, domain {domain}")
        probe_results = await HTTPProber.probe_domain(domain)
        total_probes = len(probe_results)
        logger.info(f"Completed {total_probes} HTTP probes for {domain}")

        tasks[task_id] = TaskStatus(task_id=task_id, status="completed", progress=100, probes=probe_results)
    except Exception as e:
        logger.exception(f"Error probing HTTP for {domain}: {str(e)}")
        tasks[task_id] = TaskStatus(task_id=task_id, status="failed", error=str(e))

@router.get("/probe/status/{task_id}", response_model=TaskStatus)
async def get_probe_status(task_id: str):
    if task_id not in tasks:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@router.get("/probe/results/{domain}", response_model=List[HTTPProbeResponse])
async def get_probe_results(domain: str):
    logger.info(f"Retrieving HTTP probe results for domain: {domain}")
    db = SessionLocal()
    try:
        results = get_http_probe_results(db, domain)
        if not results:
            logger.warning(f"No HTTP probe results found for domain: {domain}")
            raise HTTPException(status_code=404, detail="No HTTP probe results found for this domain")
        logger.info(f"Retrieved {len(results)} HTTP probe results for {domain}")
        return [HTTPProbeResponse(
            subdomain=result.HTTPProbeResult.subdomain.subdomain,
            url=result.HTTPProbeResult.url,
            status_code=result.HTTPProbeResult.status_code,
            title=result.HTTPProbeResult.title,
            content_length=result.HTTPProbeResult.content_length,
            technologies=result.HTTPProbeResult.technologies,
            webserver=result.HTTPProbeResult.webserver,
            cdn_name=result.HTTPProbeResult.cdn_name,
            cdn_type=result.HTTPProbeResult.cdn_type,
            ip_address=result.ip_address,
            response_time=result.HTTPProbeResult.response_time,
            created_at=result.HTTPProbeResult.created_at
        ) for result in results]
    finally:
        db.close()

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