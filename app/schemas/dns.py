# app/schemas/dns.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict
import time

class DNSResolutionBase(BaseModel):
    domain: str

class DNSResolutionCreate(DNSResolutionBase):
    pass

class DNSResolutionInDB(DNSResolutionBase):
    id: int
    subdomain_id: int
    resolved_domain: str
    ip_address: Optional[str]
    ttl: Optional[int]
    raw_data: Dict
    created_at: datetime

    class Config:
        from_attributes = True

class DNSResolutionResponse(BaseModel):
    subdomain: str
    resolved_domain: str
    ip_address: Optional[str]
    ttl: Optional[int]
    created_at: datetime

class TaskBase(BaseModel):
    task_id: str

class TaskCreate(TaskBase):
    pass

class TaskStatus(TaskBase):
    status: str
    progress: Optional[int] = None
    resolutions: Optional[List[Dict]] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

class TaskResponse(TaskBase):
    pass

class SubdomainWithResolutions(BaseModel):
    subdomain: str
    resolutions: List[DNSResolutionResponse]

class DomainResolutionsResponse(BaseModel):
    domain: str
    subdomains: List[SubdomainWithResolutions]