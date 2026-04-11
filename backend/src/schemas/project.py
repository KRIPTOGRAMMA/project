from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description='name of project')
    description: Optional[str] = Field(None, max_length=1000, description='description')
    color: str = Field(default="#3B82F6", description="HEX цвет (#RRGGBB)")

class ProjectCreate(ProjectBase):
    pass 

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = None
    is_archived: Optional[bool] = None

class ProjectResponse(ProjectBase):
    id: UUID
    workspace_id: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True