import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.database import get_db
from app.models.backlog import BACKLOG_STATUSES, DEPENDENCY_TYPES, PRIORITIES, WORK_ITEM_TYPES, WorkItem, WorkItemDependency
from app.models.organization import TeamMember
from app.models.sprint import SprintItem
from app.models.user import User
from app.services.authorization import get_project
from app.services.backlog import next_item_key, readiness_warnings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def project_or_403(request: Request, db: Session, user: User):
    project = get_project(db, user, request.session.get("project_id"))
    if not project:
        raise HTTPException(403, "Select an authorized project")
    return project


def owned_item(db: Session, project_id, item_id: str) -> WorkItem:
    try:
        value = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(404)
    item = db.scalar(select(WorkItem).where(WorkItem.id == value, WorkItem.project_id == project_id, WorkItem.archived.is_(False)))
    if not item:
        raise HTTPException(404)
    return item


@router.get("/backlog", include_in_schema=False)
def backlog_page(request: Request, q: str = "", status: str = "", item_type: str = "", priority: str = "", assignee: str = "", user: User = Depends(require_user), db: Session = Depends(get_db)):
    project = project_or_403(request, db, user)
    query = select(WorkItem).where(WorkItem.project_id == project.id, WorkItem.archived.is_(False))
    if q:
        query = query.where(or_(WorkItem.title.ilike(f"%{q}%"), WorkItem.item_key.ilike(f"%{q}%")))
    if status in BACKLOG_STATUSES: query = query.where(WorkItem.status == status)
    if item_type in WORK_ITEM_TYPES: query = query.where(WorkItem.type == item_type)
    if priority in PRIORITIES: query = query.where(WorkItem.priority == priority)
    if assignee:
        try: query = query.where(WorkItem.assignee_id == uuid.UUID(assignee))
        except ValueError: pass
    items = db.scalars(query.order_by(WorkItem.created_at.desc())).all()
    team = db.scalars(select(TeamMember).where(TeamMember.project_id == project.id, TeamMember.active.is_(True))).all()
    warnings = {item.id: readiness_warnings(db, item) for item in items}
    return templates.TemplateResponse(request, "backlog.html", {"page_title": "Backlog", "show_nav": True, "user": user, "csrf_token": csrf_token(request), "project": project, "items": items, "team": team, "warnings": warnings, "types": WORK_ITEM_TYPES, "statuses": BACKLOG_STATUSES, "priorities": PRIORITIES})


@router.post("/backlog", include_in_schema=False)
def create_item(request: Request, title: str = Form(), item_type: str = Form(alias="type"), priority: str = Form(), csrf: str = Form(), description: str = Form(default=""), acceptance_criteria: str = Form(default=""), story_points: str = Form(default=""), status_value: str = Form(alias="status", default="Backlog"), assignee_id: str = Form(default=""), epic_id: str = Form(default=""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    project = project_or_403(request, db, user)
    if item_type not in WORK_ITEM_TYPES or priority not in PRIORITIES or status_value not in BACKLOG_STATUSES:
        raise HTTPException(400)
    item = WorkItem(project_id=project.id, item_key=next_item_key(db, project), type=item_type, title=title.strip(), description=description.strip() or None, acceptance_criteria=acceptance_criteria.strip() or None, priority=priority, story_points=int(story_points) if story_points else None, status=status_value, assignee_id=uuid.UUID(assignee_id) if assignee_id else None, reporter_id=user.id, epic_id=uuid.UUID(epic_id) if epic_id else None)
    db.add(item); db.commit(); db.refresh(item)
    return RedirectResponse(f"/backlog/{item.id}", status_code=303)


@router.get("/backlog/{item_id}", include_in_schema=False)
def item_detail(request: Request, item_id: str, dependency_error: str = "", user: User = Depends(require_user), db: Session = Depends(get_db)):
    project = project_or_403(request, db, user); item = owned_item(db, project.id, item_id)
    team = db.scalars(select(TeamMember).where(TeamMember.project_id == project.id)).all()
    targets = db.scalars(select(WorkItem).where(WorkItem.project_id == project.id, WorkItem.id != item.id, WorkItem.archived.is_(False))).all()
    dependencies = db.execute(select(WorkItemDependency, WorkItem).join(WorkItem, WorkItem.id == WorkItemDependency.target_item_id).where(WorkItemDependency.source_item_id == item.id)).all()
    error_message = "Select a valid target backlog item." if dependency_error else ""
    epics = db.scalars(select(WorkItem).where(WorkItem.project_id == project.id, WorkItem.type == "Epic", WorkItem.id != item.id, WorkItem.archived.is_(False))).all()
    return templates.TemplateResponse(request, "work_item.html", {"page_title": item.item_key, "show_nav": True, "user": user, "csrf_token": csrf_token(request), "project": project, "item": item, "team": team, "targets": targets, "epics": epics, "dependencies": dependencies, "dependency_error": error_message, "warnings": readiness_warnings(db, item), "types": WORK_ITEM_TYPES, "statuses": BACKLOG_STATUSES, "priorities": PRIORITIES, "relations": DEPENDENCY_TYPES})


@router.post("/backlog/{item_id}", include_in_schema=False)
def update_item(request: Request, item_id: str, title: str = Form(), item_type: str = Form(alias="type"), priority: str = Form(), status_value: str = Form(alias="status"), csrf: str = Form(), description: str = Form(default=""), acceptance_criteria: str = Form(default=""), story_points: str = Form(default=""), assignee_id: str = Form(default=""), epic_id: str = Form(default=""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); item = owned_item(db, project.id, item_id)
    if item_type not in WORK_ITEM_TYPES or priority not in PRIORITIES or status_value not in BACKLOG_STATUSES:
        raise HTTPException(400)
    epic = owned_item(db, project.id, epic_id) if epic_id and item_type != "Epic" else None
    if epic and epic.type != "Epic": raise HTTPException(400)
    item.title, item.type, item.priority, item.status = title.strip(), item_type, priority, status_value
    item.description, item.acceptance_criteria = description.strip() or None, acceptance_criteria.strip() or None
    item.story_points, item.assignee_id = int(story_points) if story_points else None, uuid.UUID(assignee_id) if assignee_id else None
    item.epic_id = epic.id if epic else None
    db.commit(); return RedirectResponse(f"/backlog/{item.id}", status_code=303)


@router.post("/backlog/{item_id}/dependencies", include_in_schema=False)
def add_dependency(request: Request, item_id: str, csrf: str = Form(), target_item_id: str = Form(default=""), relation_type: str = Form(default=""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); item = owned_item(db, project.id, item_id)
    if not target_item_id or relation_type not in DEPENDENCY_TYPES:
        return RedirectResponse(f"/backlog/{item.id}?dependency_error=1", status_code=303)
    try:
        target = owned_item(db, project.id, target_item_id)
    except HTTPException:
        return RedirectResponse(f"/backlog/{item.id}?dependency_error=1", status_code=303)
    if item.id == target.id:
        return RedirectResponse(f"/backlog/{item.id}?dependency_error=1", status_code=303)
    existing = db.scalar(select(WorkItemDependency.id).where(WorkItemDependency.source_item_id == item.id, WorkItemDependency.target_item_id == target.id, WorkItemDependency.relation_type == relation_type))
    if not existing:
        db.add(WorkItemDependency(source_item_id=item.id, target_item_id=target.id, relation_type=relation_type)); db.commit()
    return RedirectResponse(f"/backlog/{item.id}", status_code=303)


@router.post("/backlog/{item_id}/archive", include_in_schema=False)
def archive_item(request: Request, item_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); item = owned_item(db, project.id, item_id); item.archived = True; db.commit()
    return RedirectResponse("/backlog", status_code=303)


@router.post("/backlog/{item_id}/delete", include_in_schema=False)
def delete_item(request: Request, item_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); item = owned_item(db, project.id, item_id)
    db.execute(delete(SprintItem).where(SprintItem.work_item_id == item.id)); db.delete(item); db.commit()
    return RedirectResponse("/backlog", status_code=303)
