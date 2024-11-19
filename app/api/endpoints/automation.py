# app/api/endpoints/automation.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.recon_automation import ReconAutomation
from app.schemas.automation import AutomationRequest, AutomationResponse, AutomationTaskStatus
import uuid
import logging

router = APIRouter()
logger = logging.getLogger("bbrf")

tasks = {}

@router.post("/basic-recon", response_model=AutomationResponse)
async def run_basic_recon(request: AutomationRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_recon_task, task_id, request.domain)
    return AutomationResponse(task_id=task_id, message="Basic recon started")

async def run_recon_task(task_id: str, domain: str):
    try:
        tasks[task_id] = AutomationTaskStatus(task_id=task_id, status="in_progress")
        result = await ReconAutomation.basic_recon(domain)
        logger.info(f"Recon result for {domain}: {result}")
        tasks[task_id] = AutomationTaskStatus(task_id=task_id, status="completed", result=result)
    except Exception as e:
        logger.exception(f"Error during basic recon for {domain}: {str(e)}")
        tasks[task_id] = AutomationTaskStatus(task_id=task_id, status="failed", error=str(e))

@router.get("/task/{task_id}", response_model=AutomationTaskStatus)
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]