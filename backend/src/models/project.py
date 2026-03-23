from sqlalchemy import String, Boolean, DateTime, text, ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from src.core.db import Base
from datetime import datetime
from uuid import UUID
from src.models.workspace import Workspace

class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()')
    )

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('workspaces.id', ondelete='CASCADE'),
        nullable=False    
    )
    workspace: Mapped[Workspace] = relationship('Workspace', back_populates='projects')

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(7), server_default=text("#3B82F6"))
    is_archived: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now() ,nullable=False)