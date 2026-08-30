from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.backlog import BACKLOG_STATUSES, WorkItem
from app.models.organization import TeamMember
from app.models.sprint import Sprint, SprintItem


def agile_reports(db: Session, project_id, sprint: Sprint | None, history: dict) -> dict:
    backlog = db.scalars(select(WorkItem).where(WorkItem.project_id == project_id, WorkItem.archived.is_(False))).all()
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == project_id)).all()
    member_names = {member.id: member.display_name for member in members}
    sprint_items = []
    if sprint:
        sprint_items = db.scalars(select(WorkItem).join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))).all()

    status_points = {status: 0 for status in BACKLOG_STATUSES}
    status_counts = {status: 0 for status in BACKLOG_STATUSES}
    for item in sprint_items:
        status_points[item.status] = status_points.get(item.status, 0) + (item.story_points or 0)
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
    total_points = sum(status_points.values())
    flow = [{"status": status, "count": status_counts[status], "points": status_points[status], "percent": round(status_points[status] / max(1, total_points) * 100)} for status in BACKLOG_STATUSES if status_counts[status]]

    workload = defaultdict(lambda: {"items": 0, "points": 0, "done": 0})
    for item in sprint_items:
        row = workload[member_names.get(item.assignee_id, "Unassigned")]
        row["items"] += 1; row["points"] += item.story_points or 0
        if item.status == "Done": row["done"] += item.story_points or 0
    workload_rows = [{"name": name, **values, "percent": round(values["points"] / max(1, total_points) * 100)} for name, values in sorted(workload.items())]

    children = defaultdict(list)
    for item in backlog:
        if item.epic_id: children[item.epic_id].append(item)
    epics = []
    for epic in [item for item in backlog if item.type == "Epic"]:
        scoped = children[epic.id]; points = sum(item.story_points or 0 for item in scoped); done = sum(item.story_points or 0 for item in scoped if item.status == "Done")
        epics.append({"key": epic.item_key, "title": epic.title, "items": len(scoped), "points": points, "done": done, "percent": round(done / max(1, points) * 100)})

    elapsed = 0; ideal_remaining = total_points; actual_remaining = max(0, total_points - status_points.get("Done", 0))
    if sprint:
        duration = max(1, (sprint.end_date - sprint.start_date).days + 1); elapsed = min(duration, max(0, (date.today() - sprint.start_date).days + 1)); ideal_remaining = round(total_points * max(0, duration - elapsed) / duration)
    return {"flow": flow, "workload": workload_rows, "epics": epics, "velocity": history["sprints"][-8:], "sprint": sprint, "total_points": total_points, "done_points": status_points.get("Done", 0), "remaining_points": actual_remaining, "ideal_remaining": ideal_remaining, "elapsed_days": elapsed, "backlog_count": len(backlog)}
