
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
 
from src.core.db import get_async_session
from src.core.dependencies import get_current_user
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.models.project import Project
from src.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
 
router = APIRouter(tags=["projects"])

async def check_workspace_access(
    workspace_id: UUID,
    current_user: User,
    db: AsyncSession,
    required_role: str = None
) -> WorkspaceMember:
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) & 
            (WorkspaceMember.user_id == current_user.id)
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    if required_role:
        role_hierarchy = {
            WorkspaceRole.owner.value: 4,
            WorkspaceRole.admin.value: 3,
            WorkspaceRole.member.value: 2,
            WorkspaceRole.viewer.value: 1,
        }
        
        if role_hierarchy.get(member.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You need at least {required_role} role to perform this action"
            )
    
    return member

@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    await check_workspace_access(workspace_id, current_user, db)
    
    result = await db.execute(
        select(Project).where(
            Project.workspace_id == workspace_id 
        ).offset(skip).limit(limit)
    )
    projects = result.scalars().all()
    
    return projects
 
 
@router.post("/workspaces/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    workspace_id: UUID,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    await check_workspace_access(
        workspace_id,
        current_user,
        db,
        required_role=WorkspaceRole.admin.value
    )
    
    project = Project(
        workspace_id=workspace_id,
        name=project_data.name,
        description=project_data.description,
        color=project_data.color
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project
 
 
@router.get("/workspaces/{workspace_id}/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    workspace_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    await check_workspace_access(workspace_id, current_user, db)
    
    result = await db.execute(
        select(Project).where(
            (Project.id == project_id) & 
            (Project.workspace_id == workspace_id) 
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project
 
 
@router.patch("/workspaces/{workspace_id}/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    workspace_id: UUID,
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    await check_workspace_access(
        workspace_id,
        current_user,
        db,
        required_role=WorkspaceRole.admin.value
    )
    
    result = await db.execute(
        select(Project).where(
            (Project.id == project_id) & 
            (Project.workspace_id == workspace_id) 
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project_update.name:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.color:
        project.color = project_update.color
    if project_update.is_archived is not None:
        project.is_archived = project_update.is_archived
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project
 
 
@router.delete("/workspaces/{workspace_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    workspace_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    await check_workspace_access(
        workspace_id,
        current_user,
        db,
        required_role=WorkspaceRole.admin.value
    )
    
    result = await db.execute(
        select(Project).where(
            (Project.id == project_id) & 
            (Project.workspace_id == workspace_id) 
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await db.delete(project)
    await db.commit()