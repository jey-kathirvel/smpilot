"""Link daily stand-ups directly to team members."""
from alembic import op
import sqlalchemy as sa

revision = "20260829_0012"
down_revision = "20260828_0011"

def upgrade():
    op.add_column("daily_standups", sa.Column("team_member_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_daily_standups_team_member", "daily_standups", "team_members", ["team_member_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_daily_standups_team_member_id", "daily_standups", ["team_member_id"])
    op.alter_column("daily_standups", "user_id", existing_type=sa.Uuid(), nullable=True)
    op.execute("""UPDATE daily_standups d SET team_member_id = t.id FROM team_members t WHERE d.project_id = t.project_id AND d.user_id = t.user_id AND d.team_member_id IS NULL""")
    op.create_unique_constraint("uq_daily_standup_member_date", "daily_standups", ["project_id", "team_member_id", "update_date"])

def downgrade():
    op.drop_constraint("uq_daily_standup_member_date", "daily_standups", type_="unique")
    op.drop_index("ix_daily_standups_team_member_id", table_name="daily_standups")
    op.drop_constraint("fk_daily_standups_team_member", "daily_standups", type_="foreignkey")
    op.drop_column("daily_standups", "team_member_id")
    op.alter_column("daily_standups", "user_id", existing_type=sa.Uuid(), nullable=False)
