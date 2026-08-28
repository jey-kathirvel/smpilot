"""Add sprint lifecycle.

Revision ID: 20260828_0004
Revises: 20260828_0003
"""
from alembic import op
import sqlalchemy as sa

revision = "20260828_0004"
down_revision = "20260828_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("sprints", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("goal", sa.Text()), sa.Column("start_date", sa.Date(), nullable=False), sa.Column("end_date", sa.Date(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("planned_points", sa.Integer(), nullable=False), sa.Column("completed_points", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_sprints_project_id", "sprints", ["project_id"])
    op.create_table("sprint_items", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("sprint_id", sa.Uuid(), sa.ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False), sa.Column("work_item_id", sa.Uuid(), sa.ForeignKey("work_items.id", ondelete="RESTRICT"), nullable=False), sa.Column("added_at", sa.DateTime(timezone=True), nullable=False), sa.Column("removed_at", sa.DateTime(timezone=True)), sa.Column("final_status", sa.String(30)), sa.UniqueConstraint("sprint_id", "work_item_id"))
    op.create_index("ix_sprint_items_sprint_id", "sprint_items", ["sprint_id"])
    op.create_index("ix_sprint_items_work_item_id", "sprint_items", ["work_item_id"])


def downgrade() -> None:
    op.drop_table("sprint_items")
    op.drop_table("sprints")
