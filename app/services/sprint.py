from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.backlog import WorkItem
from app.models.organization import TeamMember
from app.models.sprint import Sprint, SprintItem


def recalculate_sprint(db: Session, sprint: Sprint) -> None:
    items = db.scalars(select(WorkItem).join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))).all()
    sprint.planned_points = sum(item.story_points or 0 for item in items)
    sprint.completed_points = sum(item.story_points or 0 for item in items if item.status == "Done")


def sprint_capacity(db: Session, sprint: Sprint) -> dict[str, float]:
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == sprint.project_id, TeamMember.active.is_(True))).all()
    days = [sprint.start_date + timedelta(days=offset) for offset in range((sprint.end_date - sprint.start_date).days + 1)]
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = sum(member.capacity_hours_per_day for member in members for day in days if labels[day.weekday()] in member.working_days)
    point_capacity = hours / 6 if hours else 0
    utilization = (sprint.planned_points / point_capacity * 100) if point_capacity else 0
    return {"hours": round(hours, 1), "point_capacity": round(point_capacity, 1), "utilization": round(utilization, 1)}
