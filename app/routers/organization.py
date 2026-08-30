import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.database import get_db
from app.models.organization import ROLES, Project, TeamMember, Workspace, WorkspaceMember
from app.models.user import User
from app.services.authorization import authorized_workspaces, get_project, get_workspace

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def context(request: Request, user: User, **values):
    return {"show_nav": True, "user": user, "csrf_token": csrf_token(request), "roles": ROLES, **values}


@router.get("/settings/workspace", include_in_schema=False)
def workspace_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    workspaces = authorized_workspaces(db, user)
    selected = None if request.query_params.get("new") else get_workspace(db, user, request.query_params.get("edit_id") or request.session.get("workspace_id"))
    return templates.TemplateResponse(request, "workspace.html", context(request, user, page_title="Workspace", workspaces=workspaces, workspace=selected))


@router.post("/settings/workspace", include_in_schema=False)
def save_workspace(request: Request, name: str = Form(), csrf: str = Form(), timezone: str = Form(default="UTC"), workspace_id: str = Form(default=""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    workspace = get_workspace(db, user, workspace_id) if workspace_id else None
    if workspace:
        if workspace.owner_user_id != user.id:
            raise HTTPException(403)
        workspace.name, workspace.timezone = name.strip(), timezone.strip() or "UTC"
    else:
        workspace = Workspace(name=name.strip(), timezone=timezone.strip() or "UTC", owner_user_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="Admin"))
    db.commit()
    request.session["workspace_id"] = str(workspace.id)
    return RedirectResponse("/settings/workspace", status_code=303)


@router.post("/settings/workspace/{workspace_id}/delete", include_in_schema=False)
def delete_workspace(request: Request, workspace_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); workspace = get_workspace(db, user, workspace_id)
    if not workspace or workspace.owner_user_id != user.id: raise HTTPException(403)
    db.delete(workspace); db.commit(); request.session.pop("workspace_id", None); request.session.pop("project_id", None)
    return RedirectResponse("/settings/workspace", status_code=303)


@router.post("/settings/workspace/select", include_in_schema=False)
def select_workspace(request: Request, workspace_id: str = Form(), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    workspace = get_workspace(db, user, workspace_id)
    if not workspace:
        raise HTTPException(403)
    request.session["workspace_id"] = str(workspace.id)
    request.session.pop("project_id", None)
    return RedirectResponse("/settings/workspace", status_code=303)


@router.get("/settings/projects", include_in_schema=False)
def projects_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    workspace = get_workspace(db, user, request.session.get("workspace_id"))
    projects = db.scalars(select(Project).where(Project.workspace_id == workspace.id).order_by(Project.name)).all() if workspace else []
    editing = get_project(db, user, request.query_params.get("edit_id")) if request.query_params.get("edit_id") else None
    if editing and (not workspace or editing.workspace_id != workspace.id):
        editing = None
    return templates.TemplateResponse(request, "projects.html", context(request, user, page_title="Projects", workspace=workspace, projects=projects, editing=editing))


@router.post("/settings/projects", include_in_schema=False)
def save_project(request: Request, name: str = Form(), project_key: str = Form(), csrf: str = Form(), description: str = Form(default=""), status_value: str = Form(alias="status", default="Active"), project_id: str = Form(default=""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    workspace = get_workspace(db, user, request.session.get("workspace_id"))
    if not workspace:
        raise HTTPException(403)
    project = get_project(db, user, project_id) if project_id else None
    if project and project.workspace_id != workspace.id:
        raise HTTPException(403)
    if not project:
        project = Project(workspace_id=workspace.id)
        db.add(project)
    project.name, project.project_key = name.strip(), project_key.strip().upper()
    project.description, project.status = description.strip() or None, status_value
    db.commit()
    request.session["project_id"] = str(project.id)
    return RedirectResponse("/settings/projects", status_code=303)


@router.post("/settings/projects/{project_id}/delete", include_in_schema=False)
def delete_project(request: Request, project_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = get_project(db, user, project_id)
    if not project: raise HTTPException(403)
    workspace = get_workspace(db, user, project.workspace_id)
    if not workspace or workspace.owner_user_id != user.id: raise HTTPException(403)
    db.delete(project); db.commit()
    if request.session.get("project_id") == str(project.id): request.session.pop("project_id", None)
    return RedirectResponse("/settings/projects", status_code=303)


@router.post("/settings/projects/select", include_in_schema=False)
def select_project(request: Request, project_id: str = Form(), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    project = get_project(db, user, project_id)
    if not project:
        raise HTTPException(403)
    request.session["workspace_id"], request.session["project_id"] = str(project.workspace_id), str(project.id)
    return RedirectResponse("/team", status_code=303)


@router.get("/team", include_in_schema=False)
def team_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    project = get_project(db, user, request.session.get("project_id"))
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == project.id).order_by(TeamMember.display_name)).all() if project else []
    try: editing_id = uuid.UUID(request.query_params.get("edit_id")) if request.query_params.get("edit_id") else None
    except ValueError: editing_id = None
    editing = db.scalar(select(TeamMember).where(TeamMember.id == editing_id, TeamMember.project_id == project.id)) if project and editing_id else None
    return templates.TemplateResponse(request, "team.html", context(request, user, page_title="Team", project=project, members=members, editing=editing))


@router.post("/team", include_in_schema=False)
def save_team_member(request: Request, display_name: str = Form(), role: str = Form(), capacity_hours_per_day: float = Form(), csrf: str = Form(), working_days: list[str] = Form(default=[]), active: bool = Form(default=False), member_id: str = Form(default=""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    project = get_project(db, user, request.session.get("project_id"))
    if not project or role not in ROLES:
        raise HTTPException(403)
    member = None
    if member_id:
        try: value = uuid.UUID(member_id)
        except ValueError: raise HTTPException(404)
        member = db.scalar(select(TeamMember).where(TeamMember.id == value, TeamMember.project_id == project.id))
        if not member: raise HTTPException(404)
    if not member:
        member = TeamMember(workspace_id=project.workspace_id, project_id=project.id)
        db.add(member)
    member.display_name, member.role = display_name.strip(), role
    member.capacity_hours_per_day = max(0, min(capacity_hours_per_day, 24))
    member.working_days, member.active = working_days or ["Mon", "Tue", "Wed", "Thu", "Fri"], active
    db.commit()
    return RedirectResponse("/team", status_code=303)


@router.post("/team/{member_id}/delete", include_in_schema=False)
def delete_team_member(request: Request, member_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project = get_project(db, user, request.session.get("project_id"))
    if not project: raise HTTPException(403)
    try: value = uuid.UUID(member_id)
    except ValueError: raise HTTPException(404)
    member = db.scalar(select(TeamMember).where(TeamMember.id == value, TeamMember.project_id == project.id))
    if not member: raise HTTPException(404)
    db.delete(member); db.commit(); return RedirectResponse("/team", status_code=303)
