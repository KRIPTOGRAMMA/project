
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
 
from src.core.db import get_async_session
from src.core.dependencies import get_current_user
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.models.project import Project
from src.schemas.workspace import ProjectCreate, ProjectUpdate, ProjectResponse
 
router = APIRouter(tags=["projects"])