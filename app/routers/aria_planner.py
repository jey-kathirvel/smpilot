import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.context import build_project_context
from app.ai.planner import deterministic_sprint_plan
from app.ai.prompts import PROMPT_VERSIONS
from app.ai.schemas import SprintPlanRecommendation
from app.ai.service import AriaService
from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.config import get_settings
from app.database import get_db
from app.models.ai import SprintPlan
from app.models.backlog import WorkItem
from app.models.sprint import Sprint, SprintItem
from app.models.user import User
from app.services.authorization import get_project
from app.services.sprint import recalculate_sprint, sprint_capacity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def planning_context(request, db, user):
    project = get_project(db, user, request.session.get("project_id"))
    if not project: raise HTTPException(403)
    sprint = db.scalar(select(Sprint).where(Sprint.project_id == project.id, Sprint.status == "Planning").order_by(Sprint.created_at.desc()))
    if not sprint: raise HTTPException(400, "Create a planning sprint first")
    return project, sprint


@router.get("/sprint/planning", include_in_schema=False)
def planning_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    project, sprint = planning_context(request, db, user)
    plans = db.scalars(select(SprintPlan).where(SprintPlan.sprint_id == sprint.id).order_by(SprintPlan.created_at.desc())).all()
    backlog = db.scalars(select(WorkItem).where(WorkItem.project_id == project.id, WorkItem.archived.is_(False), WorkItem.status.in_(["Backlog", "Ready"]))).all()
    return templates.TemplateResponse(request, "aria_planning.html", {"page_title": "Aria Sprint Plan", "show_nav": True, "user": user, "csrf_token": csrf_token(request), "project": project, "sprint": sprint, "plans": plans, "backlog": backlog, "capacity": sprint_capacity(db, sprint)})


@router.post("/sprint/{sprint_id}/aria-plan", include_in_schema=False)
def generate_plan(request: Request, sprint_id: str, csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project, sprint = planning_context(request, db, user)
    if str(sprint.id) != sprint_id: raise HTTPException(403)
    context = build_project_context(db, project)
    context["planning_request"] = {"sprint": build_project_context(db, project, sprint)["sprint"], "capacity": sprint_capacity(db, sprint), "instruction": "Recommend sprint scope; never apply changes."}
    service = AriaService(get_settings())
    result = service.run(db, feature="sprint_planner", project_id=project.id, sprint_id=sprint.id, prompt_version=PROMPT_VERSIONS["sprint_planner"], context=context, schema=SprintPlanRecommendation, fallback=lambda: deterministic_sprint_plan(db, sprint))
    db.add(SprintPlan(project_id=project.id, sprint_id=sprint.id, generated_by_user_id=user.id, recommendation=result.model_dump(mode="json"), status="Suggested")); db.commit()
    return RedirectResponse("/sprint/planning", status_code=303)


@router.post("/sprint/plans/{plan_id}/decision", include_in_schema=False)
def decide_plan(request: Request, plan_id: str, decision: str = Form(), csrf: str = Form(), sprint_goal: str = Form(default=""), item_ids: list[str] = Form(default=[]), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf); project, sprint = planning_context(request, db, user)
    try: value = uuid.UUID(plan_id)
    except ValueError: raise HTTPException(404)
    plan = db.scalar(select(SprintPlan).where(SprintPlan.id == value, SprintPlan.project_id == project.id, SprintPlan.sprint_id == sprint.id, SprintPlan.status == "Suggested"))
    if not plan: raise HTTPException(404)
    if decision == "Dismissed":
        plan.status = "Dismissed"
    elif decision in {"Accepted", "Modified"}:
        recommended = plan.recommendation
        chosen = recommended["recommended_story_ids"] if decision == "Accepted" else item_ids
        for raw in chosen:
            try: item_uuid = uuid.UUID(raw)
            except ValueError: continue
            item = db.scalar(select(WorkItem).where(WorkItem.id == item_uuid, WorkItem.project_id == project.id, WorkItem.archived.is_(False)))
            if item and not db.scalar(select(SprintItem.id).where(SprintItem.sprint_id == sprint.id, SprintItem.work_item_id == item.id)):
                db.add(SprintItem(sprint_id=sprint.id, work_item_id=item.id)); item.status = "Ready"
        sprint.goal = (sprint_goal.strip() if decision == "Modified" else recommended["sprint_goal"]) or sprint.goal
        plan.status = decision; db.flush(); recalculate_sprint(db, sprint)
    else:
        raise HTTPException(400)
    plan.decided_at = datetime.now(UTC); db.commit()
    return RedirectResponse("/sprint/planning", status_code=303)
