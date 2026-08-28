"""Add approval-gated Aria sprint plans.

Revision ID: 20260828_0006
Revises: 20260828_0005
"""
from alembic import op
import sqlalchemy as sa

revision = "20260828_0006"
down_revision = "20260828_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("sprint_plans", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("sprint_id", sa.Uuid(), sa.ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False), sa.Column("generated_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("recommendation", sa.JSON(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("decided_at", sa.DateTime(timezone=True)))
    op.create_index("ix_sprint_plans_project_id", "sprint_plans", ["project_id"])
    op.create_index("ix_sprint_plans_sprint_id", "sprint_plans", ["sprint_id"])


def downgrade() -> None:
    op.drop_table("sprint_plans")
