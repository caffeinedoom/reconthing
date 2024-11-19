# app/schemas/http.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict
import time

class HTTPProbeBase(BaseModel):
    domain: str

class HTTPProbeCreate(HTTPProbeBase):
    pass

class HTTPProbeResponse(BaseModel):
    subdomain: str
    url: str
    status_code: Optional[int]
    title: Optional[str]
    content_length: Optional[int]
    technologies: Optional[List[str]]
    webserver: Optional[str]
    cdn_name: Optional[str]
    cdn_type: Optional[str]
    ip_address: Optional[str]
    response_time: Optional[str]
    created_at: datetime

class TaskBase(BaseModel):
    task_id: str

class TaskStatus(TaskBase):
    status: str
    progress: Optional[int] = None
    probes: Optional[List[Dict]] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

class TaskResponse(TaskBase):
    pass



class ServerInfo(BaseModel):
    status: str
    message: str

