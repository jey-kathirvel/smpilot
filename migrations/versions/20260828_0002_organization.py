"""Add workspace, project, and team management.

Revision ID: 20260828_0002
Revises: 20260828_0001
"""
from alembic import op
import sqlalchemy as sa

revision = "20260828_0002"
down_revision = "20260828_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("workspaces", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("name", sa.String(180), nullable=False), sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("timezone", sa.String(80), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_workspaces_owner_user_id", "workspaces", ["owner_user_id"])
    op.create_table("workspace_members", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(40), nullable=False), sa.UniqueConstraint("workspace_id", "user_id"))
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])
    op.create_table("projects", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(180), nullable=False), sa.Column("project_key", sa.String(12), nullable=False), sa.Column("description", sa.Text()), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("workspace_id", "project_key"))
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])
    op.create_table("team_members", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("display_name", sa.String(160), nullable=False), sa.Column("role", sa.String(40), nullable=False), sa.Column("capacity_hours_per_day", sa.Float(), nullable=False), sa.Column("working_days", sa.JSON(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False))
    op.create_index("ix_team_members_workspace_id", "team_members", ["workspace_id"])
    op.create_index("ix_team_members_project_id", "team_members", ["project_id"])


def downgrade() -> None:
    op.drop_table("team_members")
    op.drop_table("projects")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
