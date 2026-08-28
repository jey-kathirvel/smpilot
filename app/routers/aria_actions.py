import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.database import get_db
from app.models.ai import AriaAction
from app.models.sprint import Sprint
from app.models.user import User
from app.services.authorization import get_project
from app.services.risks import sprint_risks
router=APIRouter(); templates=Jinja2Templates(directory="app/templates")
TYPE_MAP={"blocked":"Remind Blocker Owner","spillover":"Recommend Scope Review","dependency":"Escalate Dependency","overloaded":"Recommend Reassignment","qa":"Schedule Focused Discussion"}
def scope(request,db,user):
    project=get_project(db,user,request.session.get("project_id"))
    if not project: raise HTTPException(403)
    return project,db.scalar(select(Sprint).where(Sprint.project_id==project.id,Sprint.status=="Active"))
@router.get("/aria/actions",include_in_schema=False)
def action_page(request:Request,user:User=Depends(require_user),db:Session=Depends(get_db)):
    project,sprint=scope(request,db,user); actions=db.scalars(select(AriaAction).where(AriaAction.project_id==project.id).order_by(AriaAction.created_at.desc())).all()
    return templates.TemplateResponse(request,"aria_actions.html",{"page_title":"Aria Actions","show_nav":True,"user":user,"csrf_token":csrf_token(request),"project":project,"sprint":sprint,"actions":actions})
@router.post("/aria/actions/generate",include_in_schema=False)
def generate(request:Request,csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
    validate_csrf(request,csrf); project,sprint=scope(request,db,user)
    if sprint:
        for risk in sprint_risks(db,sprint)[:8]:
            action_type=next((value for key,value in TYPE_MAP.items() if key in risk["title"].lower()),"Flag Story for Discussion")
            exists=db.scalar(select(AriaAction.id).where(AriaAction.project_id==project.id,AriaAction.sprint_id==sprint.id,AriaAction.title==risk["title"],AriaAction.status.in_(["Suggested","Approved"])))
            if not exists: db.add(AriaAction(project_id=project.id,sprint_id=sprint.id,action_type=action_type,title=risk["title"],description=risk["detail"],consequential=action_type in {"Recommend Scope Review","Recommend Reassignment","Escalate Dependency"},created_by_user_id=user.id))
    db.commit(); return RedirectResponse("/aria/actions",303)
@router.post("/aria/actions/{action_id}",include_in_schema=False)
def transition(request:Request,action_id:str,decision:str=Form(),result:str=Form(default=""),csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
    validate_csrf(request,csrf); project,_=scope(request,db,user)
    try: value=uuid.UUID(action_id)
    except ValueError: raise HTTPException(404)
    action=db.scalar(select(AriaAction).where(AriaAction.id==value,AriaAction.project_id==project.id))
    if not action: raise HTTPException(404)
    now=datetime.now(UTC)
    if decision=="Approved" and action.status=="Suggested": action.status="Approved"; action.approved_by_user_id=user.id; action.approved_at=now
    elif decision=="Dismissed" and action.status in {"Suggested","Approved"}: action.status="Dismissed"
    elif decision=="Executed" and action.status=="Approved": action.status="Executed"; action.executed_by_user_id=user.id; action.executed_at=now; action.result=result.strip() or "Recorded as completed by an authorized user."
    else: raise HTTPException(400)
    db.commit(); return RedirectResponse("/aria/actions",303)
