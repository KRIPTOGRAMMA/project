from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description='project name')
    description: Optional[str] = Field(None, max_length=1000, description='desc')
    color: str = Field(default='#3B82F6', description='HEX color (#RRGGBB)')

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
    
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="task name")
    description: Optional[str] = Field(None, max_length=2000, description="desc")
    status: str = Field(default="todo", description="todo, in_progress, done")
    priority: str = Field(default="medium", description="low, medium, high")
    assigned_to: Optional[UUID] = Field(None, description="user ID for assign")
    due_date: Optional[datetime] = Field(None, description="due date")

class TaskCreate(TaskBase):
    pass 

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[datetime] = None
 
 
class TaskResponse(TaskBase):
    id: UUID
    project_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 
 
class TaskDetailResponse(TaskResponse):
    pass

class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="comment text")
 
 
class TaskCommentResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
 
class TaskAttachmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    file_url: str
    file_name: str
    file_size: int
    uploaded_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
 