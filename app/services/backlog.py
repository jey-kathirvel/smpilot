from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.backlog import WorkItem, WorkItemDependency
from app.models.organization import Project


def next_item_key(db: Session, project: Project) -> str:
    count = db.scalar(select(func.count(WorkItem.id)).where(WorkItem.project_id == project.id)) or 0
    return f"{project.project_key}-{count + 1}"


def readiness_warnings(db: Session, item: WorkItem) -> list[str]:
    warnings: list[str] = []
    if item.type == "Story" and not item.acceptance_criteria:
        warnings.append("Missing acceptance criteria")
    if item.type in {"Story", "Bug"} and item.story_points is None:
        warnings.append("Missing story points")
    if item.story_points and item.story_points >= 13:
        warnings.append("Appears oversized")
    if not item.assignee_id:
        warnings.append("Not assigned")
    if db.scalar(select(func.count(WorkItemDependency.id)).where(WorkItemDependency.source_item_id == item.id, WorkItemDependency.relation_type.in_(["Blocked By", "Depends On"]))) and item.status != "Done":
        warnings.append("Has unresolved dependencies")
    return warnings
