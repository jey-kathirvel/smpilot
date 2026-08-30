from fastapi import APIRouter,Depends,HTTPException,Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.dependencies import csrf_token,require_user
from app.database import get_db
from app.models.sprint import Sprint
from app.models.user import User
from app.services.authorization import get_project
from app.services.agile_reports import agile_reports
from app.services.health import sprint_health
from app.services.history import sprint_history
router=APIRouter();templates=Jinja2Templates(directory="app/templates")
@router.get("/insights",include_in_schema=False)
def insights(request:Request,user:User=Depends(require_user),db:Session=Depends(get_db)):
 project=get_project(db,user,request.session.get("project_id"))
 if not project:raise HTTPException(403)
 current=db.scalar(select(Sprint).where(Sprint.project_id==project.id,Sprint.status=="Active").order_by(Sprint.start_date.desc()))
 if not current:current=db.scalar(select(Sprint).where(Sprint.project_id==project.id,Sprint.status=="Planning").order_by(Sprint.start_date.desc()))
 history=sprint_history(db,project.id); health=sprint_health(db,current) if current and current.status=="Active" else None; reports=agile_reports(db,project.id,current,history)
 return templates.TemplateResponse(request,"insights.html",{"page_title":"Aria Insights","show_nav":True,"user":user,"csrf_token":csrf_token(request),"history":history,"health":health,"reports":reports})
