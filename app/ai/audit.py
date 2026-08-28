from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AIAuditLog


def recent_ai_activity(db: Session, project_id, limit: int = 25) -> list[AIAuditLog]:
    return list(db.scalars(select(AIAuditLog).where(AIAuditLog.project_id == project_id).order_by(AIAuditLog.created_at.desc()).limit(limit)).all())
