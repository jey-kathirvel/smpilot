import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.database import get_db
from app.models.backlog import BACKLOG_STATUSES, WorkItem
from app.models.sprint import Sprint, SprintItem
from app.models.user import User
from app.services.authorization import get_project
from app.services.sprint import recalculate_sprint, sprint_capacity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
BOARD_COLUMNS = ("Ready", "In Progress", "Blocked", "Review", "Done")


def project_or_403(request, db, user):
    project = get_project(db, user, request.session.get("project_id"))
    if not project: raise HTTPException(403)
    return project


def sprint_or_404(db, project_id, sprint_id):
    try: value = uuid.UUID(str(sprint_id))
    except ValueError: raise HTTPException(404)
    sprint = db.scalar(select(Sprint).where(Sprint.id == value, Sprint.project_id == project_id))
    if not sprint: raise HTTPException(404)
    return sprint


@router.get("/sprint", include_in_schema=False)
def sprint_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    project = project_or_403(request, db, user)
    sprint = db.scalar(select(Sprint).where(Sprint.project_id == project.id, Sprint.status.in_(["Active", "Planning"])).order_by(Sprint.created_at.desc()))
    backlog = db.scalars(select(WorkItem).where(WorkItem.project_id == project.id, WorkItem.archived.is_(False), WorkItem.status.in_(["Backlog", "Ready"])).order_by(WorkItem.priority)).all()
    board = {column: [] for column in BOARD_COLUMNS}
    capacity = None
    if sprint:
        recalculate_sprint(db, sprint); db.commit(); capacity = sprint_capacity(db, sprint)
        items = db.scalars(select(WorkItem).join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))).all()
        for item in items: board[item.status if item.status in board else "Ready"].append(item)
    return templates.TemplateResponse(request, "sprint.html", {"page_title": "Sprint", "show_nav": True, "user": user, "csrf_token": csrf_token(request), "project": project, "sprint": sprint, "backlog": backlog, "board": board, "columns": BOARD_COLUMNS, "capacity": capacity})


@router.post("/sprint", include_in_schema=False)
def create_sprint(request: Request, name: str = Form(), goal: str = Form(), start_date: date = Form(), end_date: date = Form(), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user)
    if end_date < start_date or db.scalar(select(Sprint.id).where(Sprint.project_id == project.id, Sprint.status.in_(["Planning", "Active"]))): raise HTTPException(400)
    db.add(Sprint(project_id=project.id, name=name.strip(), goal=goal.strip() or None, start_date=start_date, end_date=end_date)); db.commit()
    return RedirectResponse("/sprint", status_code=303)


@router.post("/sprint/{sprint_id}/items", include_in_schema=False)
def add_sprint_items(request: Request, sprint_id: str, item_ids: list[str] = Form(), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); sprint = sprint_or_404(db, project.id, sprint_id)
    if sprint.status != "Planning": raise HTTPException(400)
    for raw in item_ids:
        item = db.scalar(select(WorkItem).where(WorkItem.id == uuid.UUID(raw), WorkItem.project_id == project.id, WorkItem.archived.is_(False)))
        if item and not db.scalar(select(SprintItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.work_item_id == item.id)):
            db.add(SprintItem(sprint_id=sprint.id, work_item_id=item.id)); item.status = "Ready"
    db.flush(); recalculate_sprint(db, sprint); db.commit(); return RedirectResponse("/sprint", status_code=303)


@router.post("/sprint/{sprint_id}/start", include_in_schema=False)
def start_sprint(request: Request, sprint_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); sprint = sprint_or_404(db, project.id, sprint_id)
    if sprint.status != "Planning": raise HTTPException(400)
    sprint.status = "Active"; recalculate_sprint(db, sprint); db.commit(); return RedirectResponse("/sprint", status_code=303)


@router.post("/sprint/{sprint_id}/items/{item_id}/status", include_in_schema=False)
def update_sprint_item(request: Request, sprint_id: str, item_id: str, status_value: str = Form(alias="status"), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); sprint = sprint_or_404(db, project.id, sprint_id)
    if sprint.status != "Active" or status_value not in BOARD_COLUMNS: raise HTTPException(400)
    item = db.scalar(select(WorkItem).join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(WorkItem.id == uuid.UUID(item_id), SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None)))
    if not item: raise HTTPException(404)
    item.status = status_value; recalculate_sprint(db, sprint); db.commit(); return RedirectResponse("/sprint", status_code=303)


@router.post("/sprint/{sprint_id}/complete", include_in_schema=False)
def complete_sprint(request: Request, sprint_id: str, csrf: str = Form(), unfinished_action: str = Form(default="backlog"), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = project_or_403(request, db, user); sprint = sprint_or_404(db, project.id, sprint_id)
    if sprint.status != "Active": raise HTTPException(400)
    rows = db.execute(select(SprintItem, WorkItem).join(WorkItem, WorkItem.id == SprintItem.work_item_id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))).all()
    for membership,item in rows:
        membership.final_status = item.status
        if item.status != "Done" and unfinished_action == "backlog": item.status = "Backlog"
    recalculate_sprint(db, sprint); sprint.status = "Completed"; db.commit(); return RedirectResponse("/sprint", status_code=303)
