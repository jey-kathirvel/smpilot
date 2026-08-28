"""Add product backlog.

Revision ID: 20260828_0003
Revises: 20260828_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20260828_0003"
down_revision = "20260828_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("work_items", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("item_key", sa.String(32), nullable=False), sa.Column("type", sa.String(20), nullable=False), sa.Column("title", sa.String(240), nullable=False), sa.Column("description", sa.Text()), sa.Column("acceptance_criteria", sa.Text()), sa.Column("priority", sa.String(20), nullable=False), sa.Column("story_points", sa.Integer()), sa.Column("status", sa.String(30), nullable=False), sa.Column("assignee_id", sa.Uuid(), sa.ForeignKey("team_members.id", ondelete="SET NULL")), sa.Column("reporter_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("epic_id", sa.Uuid(), sa.ForeignKey("work_items.id", ondelete="SET NULL")), sa.Column("archived", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("project_id", "item_key"))
    op.create_index("ix_work_items_project_id", "work_items", ["project_id"])
    op.create_index("ix_work_items_item_key", "work_items", ["item_key"])
    op.create_table("work_item_dependencies", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("source_item_id", sa.Uuid(), sa.ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False), sa.Column("target_item_id", sa.Uuid(), sa.ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False), sa.Column("relation_type", sa.String(30), nullable=False), sa.UniqueConstraint("source_item_id", "target_item_id", "relation_type"))
    op.create_index("ix_work_item_dependencies_source_item_id", "work_item_dependencies", ["source_item_id"])
    op.create_index("ix_work_item_dependencies_target_item_id", "work_item_dependencies", ["target_item_id"])


def downgrade() -> None:
    op.drop_table("work_item_dependencies")
    op.drop_table("work_items")
