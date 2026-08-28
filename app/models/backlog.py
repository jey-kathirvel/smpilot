import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import utcnow

WORK_ITEM_TYPES = ("Epic", "Story", "Task", "Bug")
PRIORITIES = ("Critical", "High", "Medium", "Low")
BACKLOG_STATUSES = ("Backlog", "Ready", "In Progress", "Blocked", "Review", "Done")
DEPENDENCY_TYPES = ("Blocks", "Blocked By", "Depends On", "Related To")


class WorkItem(Base):
    __tablename__ = "work_items"
    __table_args__ = (UniqueConstraint("project_id", "item_key"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    item_key: Mapped[str] = mapped_column(String(32), index=True)
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="Medium")
    story_points: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="Backlog")
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="RESTRICT"))
    epic_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class WorkItemDependency(Base):
    __tablename__ = "work_item_dependencies"
    __table_args__ = (UniqueConstraint("source_item_id", "target_item_id", "relation_type"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("work_items.id", ondelete="CASCADE"), index=True)
    target_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("work_items.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(30))
