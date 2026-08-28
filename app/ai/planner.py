from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.schemas import SprintPlanRecommendation
from app.models.backlog import WorkItem, WorkItemDependency
from app.models.sprint import Sprint, SprintItem
from app.services.backlog import readiness_warnings
from app.services.sprint import sprint_capacity

PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def deterministic_sprint_plan(db: Session, sprint: Sprint) -> SprintPlanRecommendation:
    candidates = db.scalars(select(WorkItem).where(WorkItem.project_id == sprint.project_id, WorkItem.archived.is_(False), WorkItem.status.in_(["Backlog", "Ready"]))).all()
    candidates.sort(key=lambda item: (PRIORITY_ORDER.get(item.priority, 9), item.created_at))
    completed = db.scalars(select(Sprint).where(Sprint.project_id == sprint.project_id, Sprint.status == "Completed", Sprint.id != sprint.id)).all()
    historical_velocity = mean([past.completed_points for past in completed[-3:]]) if completed else None
    capacity = sprint_capacity(db, sprint)
    point_limit = max(1, round(historical_velocity or capacity["point_capacity"]))
    selected: list[WorkItem] = []
    total = 0
    for item in candidates:
        points = item.story_points or 0
        if total + points <= point_limit or not selected:
            selected.append(item); total += points
    refinement = [item.item_key for item in candidates if readiness_warnings(db, item)]
    oversized = [item.item_key for item in candidates if (item.story_points or 0) >= 13]
    selected_ids = [item.id for item in selected]
    deps = db.scalars(select(WorkItemDependency).where(WorkItemDependency.source_item_id.in_(selected_ids))).all() if selected_ids else []
    dependency_notes = [f"{link.relation_type}: {link.source_item_id} -> {link.target_item_id}" for link in deps]
    utilization = total / capacity["point_capacity"] * 100 if capacity["point_capacity"] else 0
    risks = []
    if utilization > 100: risks.append("Recommended points exceed calculated team capacity")
    if refinement: risks.append(f"{len(refinement)} candidate items require refinement")
    goal = sprint.goal or (f"Deliver {selected[0].title}" if selected else f"Establish a ready goal for {sprint.name}")
    return SprintPlanRecommendation(sprint_goal=goal, recommended_story_ids=[str(item.id) for item in selected], recommended_story_keys=[item.item_key for item in selected], expected_story_points=total, capacity_utilization=round(utilization, 1), dependencies=dependency_notes, risks=risks, stories_requiring_refinement=refinement, stories_likely_too_large=oversized, rationale="Scope is prioritized by product priority and constrained by recent velocity or calculated team capacity.", confidence=0.7 if candidates else 0.4, requires_human_approval=True)
