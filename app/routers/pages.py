from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import csrf_token, require_user
from app.models.user import User
from app.database import get_db
from app.models.backlog import WorkItem
from app.models.organization import TeamMember
from app.models.sprint import Sprint, SprintItem
from app.models.standup import DailyStandup
from app.services.authorization import get_project
from app.services.sprint import recalculate_sprint
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=307)


@router.get("/today", include_in_schema=False)
async def today_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    project = get_project(db, user, request.session.get("project_id"))
    sprint = db.scalar(select(Sprint).where(Sprint.project_id == project.id, Sprint.status == "Active")) if project else None
    dashboard = None
    if sprint:
        recalculate_sprint(db, sprint); db.commit()
        items = db.scalars(select(WorkItem).join(SprintItem, SprintItem.work_item_id == WorkItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.removed_at.is_(None))).all()
        blockers = [item for item in items if item.status == "Blocked"]
        stale = [item for item in items if item.status not in {"Done", "Backlog"} and item.updated_at.date() <= date.today() - timedelta(days=2)]
        members = db.scalars(select(TeamMember).where(TeamMember.project_id == project.id, TeamMember.active.is_(True))).all()
        submitted = set(db.scalars(select(DailyStandup.user_id).where(DailyStandup.project_id == project.id, DailyStandup.update_date == date.today())).all())
        missing = [member for member in members if member.user_id and member.user_id not in submitted]
        total_days = max(1, (sprint.end_date - sprint.start_date).days + 1); sprint_day = min(total_days, max(1, (date.today() - sprint.start_date).days + 1))
        completion = round(sprint.completed_points / sprint.planned_points * 100) if sprint.planned_points else 0
        status = "CRITICAL" if blockers and sprint_day / total_days > .75 else "AT_RISK" if blockers or stale or completion + 15 < sprint_day / total_days * 100 else "ON_TRACK"
        dashboard = {"sprint_day": sprint_day, "total_days": total_days, "completion": completion, "remaining_points": max(0, sprint.planned_points - sprint.completed_points), "blockers": blockers, "stale": stale, "missing": missing, "health": status, "forecast": "Likely to complete" if status == "ON_TRACK" else "Delivery needs attention", "attention_count": len(blockers) + len(stale) + len(missing)}
    return templates.TemplateResponse(
        request,
        "today.html",
        {"page_title": "Today", "show_nav": True, "user": user, "csrf_token": csrf_token(request), "project": project, "sprint": sprint, "dashboard": dashboard},
    )
