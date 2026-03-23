from sqlalchemy import String, Boolean, DateTime, text, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from src.core.db import Base
from datetime import datetime
from uuid import UUID
from src.models.workspace import Workspace

class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,)

    workspace_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True),)
    workspace: Mapped[Workspace] = relationship('Workspace', back_populates='')

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column()
    color: Mapped[str] = mapped_column()
    is_archived: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime())
    updated_at: Mapped[datetime] = mapped_column(DateTime())