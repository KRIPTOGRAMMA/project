from src.core.db import Base
from enum import Enum
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, ForeignKey, DateTime, Enum as SAEnum, func, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.project import Project
    from src.models.user import User

class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    
class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()')
    )
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name='task_status_enum'), 
        nullable=False, 
        server_default='todo'
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, name='task_priority_enum'), 
        nullable=False, 
        server_default='medium'
    )
    assigned_to: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    project: Mapped['Project'] = relationship(
        'Project',
        back_populates='tasks',
        foreign_keys=[project_id]
    )
    
    assigned_user: Mapped[Optional['User']] = relationship(
        'User',
        back_populates='assigned_tasks',
        foreign_keys=[assigned_to]
    )
    
    creator: Mapped['User'] = relationship(
        'User',
        back_populates='created_tasks',
        foreign_keys=[created_by]
    )
    
    comments: Mapped[list['TaskComment']] = relationship(
        'TaskComment',
        back_populates='task',
        cascade='all, delete-orphan'
    )
    
    attachments: Mapped[list['TaskAttachment']] = relationship(
        'TaskAttachment',
        back_populates='task',
        cascade='all, delete-orphan'
    )

class TaskComment(Base):
    __tablename__ = 'task_comments'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()')
    )

    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'))
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    content: Mapped[Optional[str]] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    task: Mapped['Task'] = relationship(
        'Task',
        back_populates='comments',
        foreign_keys=[task_id]
    )
    
    user: Mapped['User'] = relationship(
        'User',
        back_populates='comments',
        foreign_keys=[user_id]
    )
    
class TaskAttachment(Base):
    __tablename__ = 'task_attachments'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()')
    )

    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'))
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    task: Mapped['Task'] = relationship(
        'Task',
        back_populates='attachments',
        foreign_keys=[task_id]
    )
    
    uploader: Mapped['User'] = relationship(
        'User',
        back_populates='attachments',
        foreign_keys=[uploaded_by]
    )