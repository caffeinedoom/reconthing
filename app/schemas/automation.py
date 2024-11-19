# app/schemas/automation.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class AutomationRequest(BaseModel):
    domain: str

class AutomationResponse(BaseModel):
    task_id: str
    message: str

class ReconResult(BaseModel):
    subdomains_added: int
    dns_results_added: int
    http_results_added: int

class AutomationTaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[ReconResult] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AutomationTaskDetails(BaseModel):
    domain: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    result: Optional[ReconResult] = None