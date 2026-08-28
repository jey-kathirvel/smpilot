"""Add async Daily Scrum updates and summaries."""
from alembic import op
import sqlalchemy as sa
revision="20260828_0007"; down_revision="20260828_0006"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("daily_standups", sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("project_id",sa.Uuid(),sa.ForeignKey("projects.id",ondelete="CASCADE"),nullable=False),sa.Column("sprint_id",sa.Uuid(),sa.ForeignKey("sprints.id",ondelete="SET NULL")),sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("update_date",sa.Date(),nullable=False),sa.Column("yesterday",sa.Text(),nullable=False),sa.Column("today",sa.Text(),nullable=False),sa.Column("blockers",sa.Text()),sa.Column("confidence",sa.Float()),sa.Column("status",sa.String(30),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("project_id","user_id","update_date")); op.create_index("ix_daily_standups_project_date","daily_standups",["project_id","update_date"])
    op.create_table("daily_standup_summaries",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("project_id",sa.Uuid(),sa.ForeignKey("projects.id",ondelete="CASCADE"),nullable=False),sa.Column("sprint_id",sa.Uuid(),sa.ForeignKey("sprints.id",ondelete="SET NULL")),sa.Column("summary_date",sa.Date(),nullable=False),sa.Column("analysis",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("project_id","summary_date")); op.create_index("ix_daily_standup_summaries_project_date","daily_standup_summaries",["project_id","summary_date"])
def downgrade():
    op.drop_table("daily_standup_summaries"); op.drop_table("daily_standups")
