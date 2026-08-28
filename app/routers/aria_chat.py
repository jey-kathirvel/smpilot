from fastapi import APIRouter,Depends,Form,HTTPException,Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai.context import build_project_context
from app.ai.schemas import AriaAnswer
from app.ai.service import AriaService
from app.ai.rate_limit import enforce_ai_rate_limit
from app.auth.dependencies import csrf_token,require_user,validate_csrf
from app.config import get_settings
from app.database import get_db
from app.models.ai import AriaMessage
from app.models.sprint import Sprint
from app.models.user import User
from app.services.authorization import get_project
from app.services.health import sprint_health
from app.services.risks import sprint_risks
router=APIRouter(); templates=Jinja2Templates(directory="app/templates")
def scope(request,db,user):
    project=get_project(db,user,request.session.get("project_id"))
    if not project: raise HTTPException(403)
    return project,db.scalar(select(Sprint).where(Sprint.project_id==project.id,Sprint.status=="Active"))
def fallback(db,sprint,question):
    if not sprint:return AriaAnswer(answer="There is no active sprint, so I do not have enough information to answer that yet.",supporting_facts=["No active sprint"],recommended_action="Create or start a sprint",confidence=1)
    health=sprint_health(db,sprint); risks=sprint_risks(db,sprint); facts=[f"Health is {health['status']} with score {health['score']}",f"{health['remaining_points']} points remain",f"{health['blocked_item_count']} items are blocked"]
    q=question.lower()
    if "block" in q: answer=f"The sprint has {health['blocked_item_count']} blocked item(s)."
    elif "finish" in q or "spill" in q: answer=f"The deterministic forecast is {health['status']}; {health['remaining_points']} points remain with {health['available_days']} days available."
    elif "health" in q or "orange" in q: answer="Sprint health is calculated from delivery facts, not model opinion: "+"; ".join(health["reasons"])
    elif risks: answer=f"The highest current risk is {risks[0]['title']}. {risks[0]['detail']}"
    else: answer="Focus on the sprint goal and the highest-confidence open risk."
    return AriaAnswer(answer=answer,supporting_facts=facts,recommended_action="Review the sprint risks and Action Center",confidence=1)
@router.get("/aria",include_in_schema=False)
def chat_page(request:Request,user:User=Depends(require_user),db:Session=Depends(get_db)):
    project,_=scope(request,db,user); messages=db.scalars(select(AriaMessage).where(AriaMessage.project_id==project.id,AriaMessage.user_id==user.id).order_by(AriaMessage.created_at).limit(50)).all()
    return templates.TemplateResponse(request,"aria_chat.html",{"page_title":"Ask Aria","show_nav":True,"user":user,"csrf_token":csrf_token(request),"messages":messages})
@router.post("/aria",include_in_schema=False)
def ask(request:Request,question:str=Form(),csrf:str=Form(),user:User=Depends(require_user),db:Session=Depends(get_db)):
    validate_csrf(request,csrf); settings=get_settings(); enforce_ai_rate_limit(f"{user.id}:ask_aria",requests=settings.ai_rate_limit_requests,window_seconds=settings.ai_rate_limit_window_seconds); project,sprint=scope(request,db,user); question=question.strip()[:2000]
    if not question: raise HTTPException(400)
    db.add(AriaMessage(project_id=project.id,user_id=user.id,role="user",content=question)); db.flush(); context=build_project_context(db,project,sprint); context["question"]=question
    result=AriaService(settings).run(db,feature="ask_aria",project_id=project.id,sprint_id=sprint.id if sprint else None,prompt_version="ask-aria-v1",context=context,schema=AriaAnswer,fallback=lambda:fallback(db,sprint,question))
    db.add(AriaMessage(project_id=project.id,user_id=user.id,role="assistant",content=result.answer,facts=result.model_dump(mode="json"))); db.commit(); return RedirectResponse("/aria",303)
