from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.context import build_project_context
from app.ai.prompts import ARIA_SYSTEM_PROMPT
from app.ai.schemas import DailyScrumSummary
from app.ai.service import AriaService
from app.ai.rate_limit import enforce_ai_rate_limit
from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.config import get_settings
from app.database import get_db
from app.models.sprint import Sprint
from app.models.standup import DailyStandup, DailyStandupSummary
from app.models.organization import TeamMember
from app.models.user import User
from app.services.authorization import get_project
from app.services.standup import deterministic_daily_summary
from app.services.meeting import meeting_recommendation

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/standup/meeting", include_in_schema=False)
def meeting_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    project, sprint = context(request, db, user); recommendation = meeting_recommendation(db, project.id, sprint)
    return templates.TemplateResponse(request, "meeting_recommendation.html", {"page_title": "Meeting Recommendation", "show_nav": True, "user": user, "csrf_token": csrf_token(request), "meeting": recommendation})


def context(request, db, user):
    project = get_project(db, user, request.session.get("project_id"))
    if not project: raise HTTPException(403)
    sprint = db.scalar(select(Sprint).where(Sprint.project_id == project.id, Sprint.status == "Active"))
    return project, sprint


@router.get("/standup", include_in_schema=False)
def standup_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    project, sprint = context(request, db, user); day = date.today()
    updates = db.scalars(select(DailyStandup).where(DailyStandup.project_id == project.id, DailyStandup.update_date == day).order_by(DailyStandup.created_at)).all()
    members = db.scalars(select(TeamMember).where(TeamMember.project_id == project.id, TeamMember.active.is_(True)).order_by(TeamMember.display_name)).all()
    updates_by_member = {str(member.id): next((item for item in updates if item.team_member_id == member.id or (member.user_id and item.user_id == member.user_id)), None) for member in members}
    summary = db.scalar(select(DailyStandupSummary).where(DailyStandupSummary.project_id == project.id, DailyStandupSummary.summary_date == day))
    previous_summary = db.scalar(select(DailyStandupSummary).where(DailyStandupSummary.project_id == project.id, DailyStandupSummary.summary_date < day).order_by(DailyStandupSummary.summary_date.desc()).limit(1))
    return templates.TemplateResponse(request, "standup.html", {"page_title": "Daily Scrum", "show_nav": True, "user": user, "csrf_token": csrf_token(request), "project": project, "sprint": sprint, "updates": updates, "members": members, "updates_by_member": updates_by_member, "summary": summary, "previous_summary": previous_summary})


@router.post("/standup", include_in_schema=False)
def submit_update(request: Request, team_member_id: str = Form(), yesterday: str = Form(), today: str = Form(), blockers: str = Form(default=""), confidence: float | None = Form(default=None), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project, sprint = context(request, db, user); day = date.today()
    member = db.scalar(select(TeamMember).where(TeamMember.id == team_member_id, TeamMember.project_id == project.id, TeamMember.active.is_(True)))
    if not member: raise HTTPException(404)
    identity = [DailyStandup.team_member_id == member.id]
    if member.user_id: identity.append(DailyStandup.user_id == member.user_id)
    update = db.scalar(select(DailyStandup).where(DailyStandup.project_id == project.id, DailyStandup.update_date == day, or_(*identity)))
    if not update:
        update = DailyStandup(project_id=project.id, sprint_id=sprint.id if sprint else None, user_id=member.user_id, team_member_id=member.id, update_date=day, yesterday=yesterday.strip(), today=today.strip())
        db.add(update)
    update.team_member_id, update.user_id = member.id, member.user_id
    update.yesterday, update.today, update.blockers, update.confidence, update.status = yesterday.strip(), today.strip(), blockers.strip() or None, confidence, "Submitted"
    db.commit(); return RedirectResponse("/standup", status_code=303)


@router.post("/standup/summary", include_in_schema=False)
def generate_summary(request: Request, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project, sprint = context(request, db, user); day = date.today()
    settings = get_settings(); enforce_ai_rate_limit(f"{user.id}:daily_scrum", requests=settings.ai_rate_limit_requests, window_seconds=settings.ai_rate_limit_window_seconds)
    service = AriaService(settings)
    fallback_summary = deterministic_daily_summary(db, project.id, day)
    result = service.run(db, feature="daily_scrum", project_id=project.id, sprint_id=sprint.id if sprint else None, prompt_version="daily-scrum-v2", context={"project": build_project_context(db, project, sprint), "updates": [u.__dict__ for u in db.scalars(select(DailyStandup).where(DailyStandup.project_id == project.id, DailyStandup.update_date == day)).all()], "requirement": "Return one grounded member_next_action for every active team member."}, schema=DailyScrumSummary, fallback=lambda: fallback_summary)
    generated_names = {item.member_name for item in result.member_next_actions}
    result.member_next_actions.extend(item for item in fallback_summary.member_next_actions if item.member_name not in generated_names)
    saved = db.scalar(select(DailyStandupSummary).where(DailyStandupSummary.project_id == project.id, DailyStandupSummary.summary_date == day))
    if not saved: saved = DailyStandupSummary(project_id=project.id, sprint_id=sprint.id if sprint else None, summary_date=day, analysis=result.model_dump(mode="json")); db.add(saved)
    else: saved.analysis = result.model_dump(mode="json")
    db.commit(); return RedirectResponse("/standup", status_code=303)
