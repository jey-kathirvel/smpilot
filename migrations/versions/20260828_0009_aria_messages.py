"""Add grounded Aria chat history."""
from alembic import op
import sqlalchemy as sa
revision="20260828_0009"; down_revision="20260828_0008"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("aria_messages",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("project_id",sa.Uuid(),sa.ForeignKey("projects.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("role",sa.String(20),nullable=False),sa.Column("content",sa.String(4000),nullable=False),sa.Column("facts",sa.JSON()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False)); op.create_index("ix_aria_messages_project_id","aria_messages",["project_id"]); op.create_index("ix_aria_messages_user_id","aria_messages",["user_id"])
def downgrade():op.drop_table("aria_messages")
