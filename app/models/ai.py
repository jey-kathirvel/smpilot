import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import utcnow


class AIAuditLog(Base):
    __tablename__ = "ai_audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    feature: Mapped[str] = mapped_column(String(80), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True, index=True)
    prompt_version: Mapped[str] = mapped_column(String(40))
    request_context_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict | None] = mapped_column(JSON)
    model: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SprintPlan(Base):
    __tablename__ = "sprint_plans"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    sprint_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sprints.id", ondelete="CASCADE"), index=True)
    generated_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="RESTRICT"))
    recommendation: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="Suggested")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AriaAction(Base):
    __tablename__ = "aria_actions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(80)); title: Mapped[str] = mapped_column(String(240)); description: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(30), default="Suggested"); consequential: Mapped[bool] = mapped_column(default=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True); approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True); executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); result: Mapped[str | None] = mapped_column(String(2000)); expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
