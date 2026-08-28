"""Add internal notifications."""
from alembic import op
import sqlalchemy as sa
revision="20260828_0011";down_revision="20260828_0010";branch_labels=None;depends_on=None
def upgrade():op.create_table("notifications",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("project_id",sa.Uuid(),sa.ForeignKey("projects.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("type",sa.String(60),nullable=False),sa.Column("title",sa.String(240),nullable=False),sa.Column("body",sa.String(1200),nullable=False),sa.Column("read",sa.Boolean(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_notifications_project_id","notifications",["project_id"]);op.create_index("ix_notifications_user_id","notifications",["user_id"])
def downgrade():op.drop_table("notifications")
