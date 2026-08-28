from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.schemas import DailyScrumSummary
from app.models.backlog import WorkItem
from app.models.organization import TeamMember
from app.models.standup import DailyStandup


def deterministic_daily_summary(db: Session, project_id, day: date) -> DailyScrumSummary:
    updates = db.scalars(select(DailyStandup).where(DailyStandup.project_id == project_id, DailyStandup.update_date == day)).all()
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == project_id, TeamMember.active.is_(True))).all()
    submitted = {update.user_id for update in updates}
    missing = [member.display_name for member in members if member.user_id and member.user_id not in submitted]
    stale = db.scalars(select(WorkItem).where(WorkItem.project_id == project_id, WorkItem.status.in_(["In Progress", "Blocked", "Review"]), WorkItem.updated_at < day - timedelta(days=2))).all()
    blockers = [update.blockers for update in updates if update.blockers and update.blockers.strip().lower() not in {"none", "no"}]
    return DailyScrumSummary(
        team_summary=f"{len(updates)} updates submitted; {len(missing)} still missing.",
        accomplishments=[update.yesterday for update in updates if update.yesterday],
        todays_focus=[update.today for update in updates if update.today],
        blockers=blockers,
        emerging_dependencies=[],
        missing_updates=missing,
        stale_stories=[f"{item.item_key}: {item.title}" for item in stale],
        coordination_needed=blockers,
        follow_up_suggestions=["Follow up with missing team members"] if missing else [],
        confidence=1.0,
    )
