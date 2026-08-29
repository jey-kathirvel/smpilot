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
    submitted_members = {update.team_member_id for update in updates if update.team_member_id}
    submitted_users = {update.user_id for update in updates if update.user_id}
    missing = [member.display_name for member in members if member.id not in submitted_members and (not member.user_id or member.user_id not in submitted_users)]
    stale = db.scalars(select(WorkItem).where(WorkItem.project_id == project_id, WorkItem.status.in_(["In Progress", "Blocked", "Review"]), WorkItem.updated_at < day - timedelta(days=2))).all()
    blockers = [update.blockers for update in updates if update.blockers and update.blockers.strip().lower() not in {"none", "no"}]
    actions = []
    for member in members:
        update = next((item for item in updates if item.team_member_id == member.id or (member.user_id and item.user_id == member.user_id)), None)
        assigned = db.scalars(select(WorkItem).where(WorkItem.project_id == project_id, WorkItem.assignee_id == member.id, WorkItem.status.in_(["In Progress", "Blocked", "Review"]))).all()
        if not update:
            action, rationale = "Submit the next stand-up update and confirm today's priority.", "No update was submitted."
        elif update.blockers and update.blockers.strip().lower() not in {"none", "no"}:
            action, rationale = f"Resolve or escalate: {update.blockers}", "The member reported an active blocker."
        elif assigned:
            action, rationale = f"Continue {assigned[0].item_key}: {assigned[0].title}", f"This is the member's current {assigned[0].status.lower()} sprint item."
        else:
            action, rationale = update.today, "Carried forward from the latest stand-up focus."
        actions.append({"member_name": member.display_name, "action": action, "rationale": rationale})
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
        member_next_actions=actions,
        confidence=1.0,
    )
