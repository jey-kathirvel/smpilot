import uuid
from fastapi import APIRouter,Depends,Form,HTTPException,Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.auth.dependencies import csrf_token,require_user,validate_csrf
from app.database import get_db
from app.models.notification import Notification
from app.models.sprint import Sprint
from app.models.user import User
from app.services.authorization import get_project
from app.services.health import sprint_health
router=APIRouter();templates=Jinja2Templates(directory="app/templates")
def scope(request,db,user):
 p=get_project(db,user,request.session.get("project_id"))
 if not p:raise HTTPException(403)
 return p
@router.get("/notifications",include_in_schema=False)
def page(request:Request,user:User=Depends(require_user),db:Session=Depends(get_db)):
 p=scope(request,db,user);items=db.scalars(select(Notification).where(Notification.project_id==p.id,Notification.user_id==user.id).order_by(Notification.created_at.desc())).all();return templates.TemplateResponse(request,"notifications.html",{"page_title":"Notifications","show_nav":True,"user":user,"csrf_token":csrf_token(request),"notifications":items})
@router.get("/notifications/unread-count",include_in_schema=False)
def count(request:Request,user:User=Depends(require_user),db:Session=Depends(get_db)):
 p=scope(request,db,user);return {"count":db.scalar(select(func.count()).select_from(Notification).where(Notification.project_id==p.id,Notification.user_id==user.id,Notification.read.is_(False))) or 0}
@router.post("/notifications/generate",include_in_schema=False)
def generate(request:Request,csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
 validate_csrf(request,csrf);p=scope(request,db,user);s=db.scalar(select(Sprint).where(Sprint.project_id==p.id,Sprint.status=="Active"))
 if s:
  h=sprint_health(db,s)
  if h["status"]!="ON_TRACK":db.add(Notification(project_id=p.id,user_id=user.id,type="Sprint At Risk",title=f"{s.name} is {h['status'].replace('_',' ')}",body="; ".join(h["reasons"])))
 db.commit();return RedirectResponse("/notifications",303)
@router.post("/notifications/{notification_id}/read",include_in_schema=False)
def read(request:Request,notification_id:str,csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
 validate_csrf(request,csrf);p=scope(request,db,user)
 try:value=uuid.UUID(notification_id)
 except ValueError:raise HTTPException(404)
 n=db.scalar(select(Notification).where(Notification.id==value,Notification.project_id==p.id,Notification.user_id==user.id))
 if not n:raise HTTPException(404)
 n.read=True;db.commit();return RedirectResponse("/notifications",303)
@router.post("/notifications/read-all",include_in_schema=False)
def read_all(request:Request,csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
 validate_csrf(request,csrf);p=scope(request,db,user)
 for n in db.scalars(select(Notification).where(Notification.project_id==p.id,Notification.user_id==user.id,Notification.read.is_(False))):n.read=True
 db.commit();return RedirectResponse("/notifications",303)
