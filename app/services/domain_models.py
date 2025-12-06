from pydantic import BaseModel, Field
from typing import Optional, List


class DomainInfo(BaseModel):
    name: Optional[str] = Field(None, description="Domain name")
    description: Optional[str] = Field(None, description="Domain description")
    use_case: Optional[str] = Field(None, description="Primary use case for this domain")
    target_user: Optional[str] = Field(None, description="Target user or audience")
    mcp_server_urls: Optional[List[str]] = Field(default_factory=list, description="MCP server URLs if provided")


class NextQuestion(BaseModel):
    question: str = Field(..., description="Next question to ask the user")
    is_complete: bool = Field(False, description="Whether all required information has been collected")
    reasoning: str = Field(..., description="Why this question is being asked or why onboarding is complete")