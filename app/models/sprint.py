import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import utcnow

SPRINT_STATUSES = ("Planning", "Active", "Completed", "Cancelled")


class Sprint(Base):
    __tablename__ = "sprints"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    goal: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="Planning")
    planned_points: Mapped[int] = mapped_column(Integer, default=0)
    completed_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SprintItem(Base):
    __tablename__ = "sprint_items"
    __table_args__ = (UniqueConstraint("sprint_id", "work_item_id"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sprint_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sprints.id", ondelete="CASCADE"), index=True)
    work_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("work_items.id", ondelete="RESTRICT"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_status: Mapped[str | None] = mapped_column(String(30))
