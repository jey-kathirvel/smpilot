"""Add sprint retrospective feedback and actions."""
from alembic import op
import sqlalchemy as sa
revision="20260828_0010";down_revision="20260828_0009";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("retro_feedback",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("sprint_id",sa.Uuid(),sa.ForeignKey("sprints.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("category",sa.String(30),nullable=False),sa.Column("content",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_retro_feedback_sprint_id","retro_feedback",["sprint_id"]);op.create_table("retro_actions",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("source_sprint_id",sa.Uuid(),sa.ForeignKey("sprints.id",ondelete="CASCADE"),nullable=False),sa.Column("title",sa.String(240),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("owner",sa.String(160)),sa.Column("due_date",sa.Date()),sa.Column("status",sa.String(30),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_retro_actions_source_sprint_id","retro_actions",["source_sprint_id"])
def downgrade():op.drop_table("retro_actions");op.drop_table("retro_feedback")
