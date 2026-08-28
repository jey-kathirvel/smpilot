from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.backlog import WorkItem, WorkItemDependency
from app.models.organization import Project, TeamMember
from app.models.sprint import Sprint, SprintItem


def build_project_context(db: Session, project: Project, sprint: Sprint | None = None) -> dict:
    team = db.scalars(select(TeamMember).where(TeamMember.project_id == project.id, TeamMember.active.is_(True))).all()
    items_query = select(WorkItem).where(WorkItem.project_id == project.id, WorkItem.archived.is_(False))
    if sprint:
        items_query = items_query.join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))
    items = db.scalars(items_query).all()
    item_ids = [item.id for item in items]
    dependencies = db.scalars(select(WorkItemDependency).where(WorkItemDependency.source_item_id.in_(item_ids))).all() if item_ids else []
    return {
        "project": {"id": str(project.id), "name": project.name, "key": project.project_key},
        "sprint": None if not sprint else {"id": str(sprint.id), "name": sprint.name, "goal": sprint.goal, "start_date": sprint.start_date, "end_date": sprint.end_date, "status": sprint.status, "planned_points": sprint.planned_points, "completed_points": sprint.completed_points},
        "team": [{"id": str(member.id), "name": member.display_name, "role": member.role, "capacity_hours_per_day": member.capacity_hours_per_day, "working_days": member.working_days} for member in team],
        "work_items": [{"id": str(item.id), "key": item.item_key, "type": item.type, "title": item.title, "description": item.description, "acceptance_criteria": item.acceptance_criteria, "priority": item.priority, "points": item.story_points, "status": item.status, "assignee_id": str(item.assignee_id) if item.assignee_id else None} for item in items],
        "dependencies": [{"source": str(link.source_item_id), "target": str(link.target_item_id), "type": link.relation_type} for link in dependencies],
    }
