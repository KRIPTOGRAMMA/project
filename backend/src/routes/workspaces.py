from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
 
from src.core.db import get_async_session
from src.core.dependencies import get_current_user
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
)
 
router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get('', response_model=list[WorkspaceResponse])
async def list_workspace(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Workspace).join(
            WorkspaceMember
        ).where(
            WorkspaceMember.user_id == current_user.id
        )
    )
    workspaces = result.scalars().all()

    return workspaces

@router.post('', response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=current_user.id
    )
    db.add(workspace)
    await db.flush()

    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=WorkspaceRole.owner.value
    )
    db.add(owner_member)

    await db.commit()
    await db.refresh(workspace)

    return workspace

@router.get('/{workspace_id}', response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Workspace not found'
        )
    
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
    
    return workspace

@router.patch('/{workspace_id}', response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    workspace_update: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
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
    
    if member.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can update workspace"
        )
    
    if workspace_update.name:
        workspace.name = workspace_update.name
    if workspace_update.description is not None:
        workspace.description = workspace_update.description
    if workspace_update.is_archived is not None:
        workspace.is_archived = workspace_update.is_archived
    
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    
    return workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete workspace"
        )
    
    await db.delete(workspace)
    await db.commit()

@router.get('/{workspace_id}/members', response_model=list[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
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
    
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id
        )
    )
    members = result.scalars().all()
    
    return members

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: UUID,
    member_data: WorkspaceMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) & 
            (WorkspaceMember.user_id == current_user.id) 
        )
    )
    current_member = result.scalar_one_or_none()
    
    if not current_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    if current_member.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can add members"
        )
    
    result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) &  
            (WorkspaceMember.user_id == member_data.user_id) 
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace"
        )
    
    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    
    return new_member
 
 
@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member_role(
    workspace_id: UUID,
    user_id: UUID,
    role_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can change member roles"
        )
    
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) &  
            (WorkspaceMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace"
        )
    
    new_role = role_update.get("role")
    if new_role not in [r.value for r in WorkspaceRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([r.value for r in WorkspaceRole])}"
        )
    
    member.role = new_role
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    return member
 
 
@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) &  
            (WorkspaceMember.user_id == current_user.id) 
        )
    )
    current_member = result.scalar_one_or_none()
    
    if not current_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    if current_member.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can remove members"
        )
    
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) & 
            (WorkspaceMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace"
        )
    
    await db.delete(member)
    await db.commit()