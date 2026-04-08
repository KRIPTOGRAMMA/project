from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description='name')
    description: Optional[str] = Field(None, max_length=1000, description='desc')

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_archived: Optional[bool] = None

class WorkspaceResponse(WorkspaceBase):
    id: UUID
    owner_id: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkspaceDetailResponse(WorkspaceResponse):
    pass

class WorkspaceMemberBase(BaseModel):
    role: str = Field(..., description='Role: owner, admin, member, viewer')

class WorkspaceMemberCreate(WorkspaceMemberBase):
    user_id: UUID = Field(..., description='user ID')
    role: str = Field(default='member', description='default role')

class WorkspaceMemberUpdate(BaseModel):
    role: str = Field(..., description='new role')

class WorkspaceMemberResponse(WorkspaceMemberBase):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    joined_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
class WorkspaceMemberDetailResponse(WorkspaceMemberResponse):
    pass