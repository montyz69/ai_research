from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class DomainBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    use_case: Optional[str] = None
    target_user: Optional[str] = None
    mcp_server_urls: Optional[List[str]] = []


class DomainCreate(DomainBase):
    pass


class DomainUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    use_case: Optional[str] = None
    target_user: Optional[str] = None
    mcp_server_urls: Optional[List[str]] = None


class DomainResponse(DomainBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DomainOnboardingStart(BaseModel):
    pass


class DomainOnboardingMessage(BaseModel):
    session_id: str
    message: str


class DomainOnboardingResponse(BaseModel):
    session_id: str
    question: str
    is_complete: bool = False
    collected_info: Optional[Dict[str, Any]] = None


class DomainOnboardingComplete(BaseModel):
    session_id: str