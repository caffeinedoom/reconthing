# app/schemas/subdomain.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class SubdomainBase(BaseModel):
    domain: str

class SubdomainCreate(SubdomainBase):
    pass

class SubdomainInDB(SubdomainBase):
    id: int
    subdomain: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SubdomainResponse(SubdomainInDB):
    pass

class TaskBase(BaseModel):
    task_id: str

class TaskCreate(TaskBase):
    pass

class TaskStatus(TaskBase):
    status: str
    progress: Optional[int] = None
    subdomains: Optional[List[str]] = None
    error: Optional[str] = None

class TaskResponse(TaskBase):
    pass