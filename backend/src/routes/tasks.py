from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
 
from src.core.db import get_async_session
from src.core.dependencies import get_current_user
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.models.project import Project
from src.models.task import Task, TaskComment, TaskAttachment, TaskStatus, TaskPriority
from src.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailResponse,
    TaskCommentCreate,
    TaskCommentResponse,
)
 
router = APIRouter(tags=["tasks"])

async def check_project_access(
    project_id: UUID,
    current_user: User,
    db: AsyncSession
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found'
        )
    
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == project.workspace_id) &
            (WorkspaceMember.user_id == current_user.id)
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    return project

@router.get('projects/{project_id}/tasks', response_model=list[TaskResponse])
async def list_tasks(
    project_id: UUID,
    status: str = Query(None, description="Фильтр по статусу: todo, in_progress, done"),
    priority: str = Query(None, description="Фильтр по приоритету: low, medium, high"),
    assigned_to: UUID = Query(None, description="Фильтр по назначенному юзеру"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await check_project_access(project_id, current_user, db)

    query = select(Task).where(Task.project_id == project_id)

    if status:
        query = query.where(Task.status == status)
    
    if priority:
        query = query.where(Task.priority == priority)
    
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)  

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return tasks

@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: UUID,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await check_project_access(project_id, current_user, db)

    valid_statuses = [s.value for s in TaskStatus]
    valid_priorities = [p.value for p in TaskPriority]

    if task_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    if task_data.priority not in valid_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )
    
    if task_data.assigned_to:
        result = await db.execute(
            select(User).where(User.id == task_data.assigned_to)
        )
        assigned_user = result.scalar_one_or_none()
        
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found"
            )
        
        result = await db.execute(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == project.workspace_id) &  
                (WorkspaceMember.user_id == task_data.assigned_to) 
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a member of this workspace"
            )
    
    task = Task(
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        assigned_to=task_data.assigned_to,
        created_by=current_user.id,
        due_date=task_data.due_date
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return task
 
@router.get('/projects/{project_id}/tasks/{task_id}', response_model=TaskDetailResponse)
async def get_task(
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await check_project_access(project_id, current_user, db)

    result = await db.execute(
        select(Task).where(
            (Task.id == task_id) &
            (Task.project_id == project_id)
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Task not found'
        )
    
    return task

@router.patch('/projects/{project_id}/tasks/{task_id}', response_model=TaskResponse)
async def update_task(
    project_id: UUID,
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await check_project_access(project_id, current_user, db)

    result = await db.execute(
        select(Task).where(
            (Task.id == task_id) & 
            (Task.project_id == project_id)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.created_by != current_user.id:
        result = await db.execute(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == project.workspace_id) &  
                (WorkspaceMember.user_id == current_user.id)
            )
        )
        member = result.scalar_one_or_none()
        
        if not member or member.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only creator or workspace admin can update this task"
            )
    
    if task_update.title:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status:
        valid_statuses = [s.value for s in TaskStatus]
        if task_update.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status"
            )
        task.status = task_update.status
    if task_update.priority:
        valid_priorities = [p.value for p in TaskPriority]
        if task_update.priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority"
            )
        task.priority = task_update.priority
    if task_update.assigned_to is not None:
        task.assigned_to = task_update.assigned_to
    if task_update.due_date is not None:
        task.due_date = task_update.due_date
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return task

@router.delete("/projects/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await check_project_access(project_id, current_user, db)
    
    result = await db.execute(
        select(Task).where(
            (Task.id == task_id) & 
            (Task.project_id == project_id)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.created_by != current_user.id:
        result = await db.execute(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == project.workspace_id) &  
                (WorkspaceMember.user_id == current_user.id) 
            )
        )
        member = result.scalar_one_or_none()
        
        if not member or member.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only creator or workspace admin can delete this task"
            )
    
    await db.delete(task)
    await db.commit()
 
@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: UUID,
    comment_data: TaskCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Task).where(Task.id == task_id) 
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    result = await db.execute(
        select(Project).where(Project.id == task.project_id)
    )
    project = result.scalar_one_or_none()
    
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == project.workspace_id) &  
            (WorkspaceMember.user_id == current_user.id) 
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task"
        )
    
    comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return comment
 
 
@router.get("/tasks/{task_id}/comments", response_model=list[TaskCommentResponse])
async def get_comments(
    task_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    result = await db.execute(
        select(TaskComment).where(
            TaskComment.task_id == task_id
        ).offset(skip).limit(limit)
    )
    comments = result.scalars().all()
    
    return comments
 
 
@router.delete("/tasks/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    task_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(TaskComment).where(
            (TaskComment.id == comment_id) &  
            (TaskComment.task_id == task_id) 
        )
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.user_id != current_user.id:
        task_result = await db.execute(
            select(Task).where(Task.id == task_id) 
        )
        task = task_result.scalar_one_or_none()
        
        project_result = await db.execute(
            select(Project).where(Project.id == task.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        member_result = await db.execute(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == project.workspace_id) &  
                (WorkspaceMember.user_id == current_user.id)
            )
        )
        member = member_result.scalar_one_or_none()
        
        if not member or member.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only comment author or workspace admin can delete"
            )
    
    await db.delete(comment)
    await db.commit()