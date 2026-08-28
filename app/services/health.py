from datetime import UTC, date, datetime, timedelta
from statistics import mean
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.backlog import WorkItem
from app.models.organization import TeamMember
from app.models.sprint import Sprint, SprintItem
from app.models.standup import DailyStandup
from app.services.sprint import recalculate_sprint, sprint_capacity


def sprint_health(db: Session, sprint: Sprint, as_of: date | None = None) -> dict:
    today = as_of or date.today(); recalculate_sprint(db, sprint)
    rows = db.execute(select(SprintItem, WorkItem).join(WorkItem, WorkItem.id == SprintItem.work_item_id).where(SprintItem.sprint_id == sprint.id)).all()
    active = [(membership, item) for membership, item in rows if membership.removed_at is None]
    total_days = max(1, (sprint.end_date - sprint.start_date).days + 1); elapsed_days = min(total_days, max(0, (today - sprint.start_date).days + 1))
    elapsed_pct = round(elapsed_days / total_days * 100, 1); completion_pct = round(sprint.completed_points / sprint.planned_points * 100, 1) if sprint.planned_points else 0.0
    blocked = [item for _, item in active if item.status == "Blocked"]; blocked_points = sum(item.story_points or 0 for item in blocked); now = datetime.now(UTC); blocker_ages = []
    for item in blocked:
        updated = item.updated_at if item.updated_at.tzinfo else item.updated_at.replace(tzinfo=UTC); blocker_ages.append(max(0, (now - updated).total_seconds() / 3600))
    stale = [item for _, item in active if item.status not in {"Done", "Backlog"} and item.updated_at.date() <= today - timedelta(days=2)]
    scope_added = sum(item.story_points or 0 for membership, item in active if membership.added_at.date() > sprint.start_date)
    scope_removed = sum(item.story_points or 0 for membership, item in rows if membership.removed_at and membership.removed_at.date() > sprint.start_date)
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == sprint.project_id, TeamMember.active.is_(True))).all(); submitted = set(db.scalars(select(DailyStandup.user_id).where(DailyStandup.project_id == sprint.project_id, DailyStandup.update_date == today)).all())
    missing_updates = sum(1 for member in members if member.user_id and member.user_id not in submitted)
    history = db.scalars(select(Sprint).where(Sprint.project_id == sprint.project_id, Sprint.status == "Completed", Sprint.id != sprint.id)).all(); velocity = round(mean([item.completed_points for item in history[-3:]]), 1) if history else 0.0; capacity = sprint_capacity(db, sprint)
    reasons = []; penalty = 0; blocked_pct = blocked_points / sprint.planned_points * 100 if sprint.planned_points else 0
    if blocked_pct >= 30: penalty += 35; reasons.append(f"{blocked_pct:.0f}% of sprint scope is blocked")
    elif blocked_pct > 0: penalty += 18; reasons.append(f"{blocked_pct:.0f}% of sprint scope is blocked")
    if elapsed_pct - completion_pct > 30: penalty += 30; reasons.append("Completion is materially behind elapsed sprint time")
    elif elapsed_pct - completion_pct > 15: penalty += 15; reasons.append("Completion is behind elapsed sprint time")
    if stale: penalty += min(15, len(stale) * 5); reasons.append(f"{len(stale)} work item(s) are stale")
    if scope_added: penalty += 10; reasons.append(f"{scope_added} points were added after sprint start")
    if missing_updates: penalty += min(10, missing_updates * 3); reasons.append(f"{missing_updates} stand-up update(s) are missing")
    score = max(0, 100 - penalty); status = "CRITICAL" if score < 50 else "AT_RISK" if score < 80 else "ON_TRACK"
    if not reasons: reasons.append("No deterministic delivery risks exceed configured thresholds")
    return {"status": status, "score": score, "reasons": reasons, "elapsed_sprint_percent": elapsed_pct, "completion_percent": completion_pct, "completed_story_points": sprint.completed_points, "remaining_points": max(0, sprint.planned_points - sprint.completed_points), "blocked_points": blocked_points, "blocked_item_count": len(blocked), "average_blocker_age_hours": round(mean(blocker_ages), 1) if blocker_ages else 0.0, "stale_work_count": len(stale), "scope_added_points": scope_added, "scope_removed_points": scope_removed, "available_days": max(0, (sprint.end_date - today).days + 1), "team_capacity_points": capacity["point_capacity"], "historical_velocity": velocity, "missing_updates": missing_updates}
