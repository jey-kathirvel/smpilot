"""Add Aria AI audit log.

Revision ID: 20260828_0005
Revises: 20260828_0004
"""
from alembic import op
import sqlalchemy as sa

revision = "20260828_0005"
down_revision = "20260828_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("ai_audit_logs", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("feature", sa.String(80), nullable=False), sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("sprint_id", sa.Uuid(), sa.ForeignKey("sprints.id", ondelete="SET NULL")), sa.Column("prompt_version", sa.String(40), nullable=False), sa.Column("request_context_hash", sa.String(64), nullable=False), sa.Column("response", sa.JSON()), sa.Column("model", sa.String(100)), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_ai_audit_logs_feature", "ai_audit_logs", ["feature"])
    op.create_index("ix_ai_audit_logs_project_id", "ai_audit_logs", ["project_id"])
    op.create_index("ix_ai_audit_logs_sprint_id", "ai_audit_logs", ["sprint_id"])


def downgrade() -> None:
    op.drop_table("ai_audit_logs")
