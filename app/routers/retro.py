import uuid
from datetime import date
from fastapi import APIRouter,Depends,Form,HTTPException,Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.dependencies import csrf_token,require_user,validate_csrf
from app.database import get_db
from app.models.backlog import WorkItem
from app.models.retro import RetroAction,RetroFeedback
from app.models.sprint import Sprint,SprintItem
from app.models.user import User
from app.services.authorization import get_project
router=APIRouter(); templates=Jinja2Templates(directory="app/templates")
def sprint_scope(request,db,user,sprint_id):
    project=get_project(db,user,request.session.get("project_id"))
    try:value=uuid.UUID(sprint_id)
    except ValueError:raise HTTPException(404)
    sprint=db.scalar(select(Sprint).where(Sprint.id==value,Sprint.project_id==project.id)) if project else None
    if not sprint:raise HTTPException(404)
    return sprint
@router.get("/sprints/{sprint_id}/review",include_in_schema=False)
def review(request:Request,sprint_id:str,user:User=Depends(require_user),db:Session=Depends(get_db)):
    sprint=sprint_scope(request,db,user,sprint_id); items=db.scalars(select(WorkItem).join(SprintItem,SprintItem.work_item_id==WorkItem.id).where(SprintItem.sprint_id==sprint.id)).all(); done=[i for i in items if i.status=="Done"]; incomplete=[i for i in items if i.status!="Done"]; pct=round(sprint.completed_points/sprint.planned_points*100) if sprint.planned_points else 0
    return templates.TemplateResponse(request,"sprint_review.html",{"page_title":"Sprint Review","show_nav":True,"user":user,"csrf_token":csrf_token(request),"sprint":sprint,"done":done,"incomplete":incomplete,"completion":pct,"summary":f"Delivered {sprint.completed_points} of {sprint.planned_points} points ({pct}%)."})
@router.get("/sprints/{sprint_id}/retro",include_in_schema=False)
def retro(request:Request,sprint_id:str,user:User=Depends(require_user),db:Session=Depends(get_db)):
    sprint=sprint_scope(request,db,user,sprint_id); feedback=db.scalars(select(RetroFeedback).where(RetroFeedback.sprint_id==sprint.id)).all(); actions=db.scalars(select(RetroAction).where(RetroAction.source_sprint_id==sprint.id)).all()
    return templates.TemplateResponse(request,"retro.html",{"page_title":"Team Retrospective","show_nav":True,"user":user,"csrf_token":csrf_token(request),"sprint":sprint,"feedback":feedback,"actions":actions,"can_complete":bool(feedback),"required":bool(request.query_params.get("required"))})
@router.post("/sprints/{sprint_id}/retro",include_in_schema=False)
def add_feedback(request:Request,sprint_id:str,category:str=Form(),content:str=Form(),csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
    validate_csrf(request,csrf); sprint=sprint_scope(request,db,user,sprint_id)
    if category not in {"Went Well","Didn't Go Well","Ideas","Actions"}:raise HTTPException(400)
    db.add(RetroFeedback(sprint_id=sprint.id,user_id=user.id,category=category,content=content.strip())); db.commit(); return RedirectResponse(f"/sprints/{sprint.id}/retro",303)
@router.post("/sprints/{sprint_id}/retro/actions",include_in_schema=False)
def add_action(request:Request,sprint_id:str,title:str=Form(),description:str=Form(),owner:str=Form(default=""),due_date:date|None=Form(default=None),csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
    validate_csrf(request,csrf); sprint=sprint_scope(request,db,user,sprint_id); db.add(RetroAction(source_sprint_id=sprint.id,title=title.strip(),description=description.strip(),owner=owner.strip() or None,due_date=due_date)); db.commit(); return RedirectResponse(f"/sprints/{sprint.id}/retro",303)
