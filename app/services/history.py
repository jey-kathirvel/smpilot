from statistics import mean
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.backlog import WorkItem
from app.models.retro import RetroAction
from app.models.sprint import Sprint,SprintItem

def sprint_history(db:Session,project_id)->dict:
    sprints=db.scalars(select(Sprint).where(Sprint.project_id==project_id,Sprint.status=="Completed").order_by(Sprint.end_date)).all(); rows=[]
    for sprint in sprints:
        memberships=db.scalars(select(SprintItem).where(SprintItem.sprint_id==sprint.id)).all(); active=[m for m in memberships if m.removed_at is None]; removed=[m for m in memberships if m.removed_at is not None]; items=db.scalars(select(WorkItem).join(SprintItem,SprintItem.work_item_id==WorkItem.id).where(SprintItem.sprint_id==sprint.id)).all(); blockers=sum(1 for m in memberships if m.final_status=="Blocked"); retro=db.scalars(select(RetroAction).where(RetroAction.source_sprint_id==sprint.id)).all(); delivered=sprint.completed_points; planned=sprint.planned_points; completion=round(delivered/planned*100,1) if planned else 0
        rows.append({"name":sprint.name,"velocity":delivered,"planned":planned,"delivered":delivered,"completion_rate":completion,"carryover_rate":round(len([i for i in items if i.status!="Done"])/max(1,len(items))*100,1),"blocker_count":blockers,"scope_added":sum(1 for m in active if m.added_at.date()>sprint.start_date),"scope_removed":len(removed),"estimation_variance":planned-delivered,"retro_completion":round(sum(1 for a in retro if a.status=="Done")/max(1,len(retro))*100,1)})
    recent=rows[-3:]; trends=[]
    if len(recent)>=2:
        old,new=recent[0],recent[-1]; change=round((new["velocity"]-old["velocity"])/max(1,old["velocity"])*100,1); trends.append(f"Velocity {'increased' if change>=0 else 'decreased'} {abs(change)}% over the recent sprint window."); trends.append(f"Carryover changed from {old['carryover_rate']}% to {new['carryover_rate']}%.")
    return {"sprints":rows,"velocity":round(mean([r["velocity"] for r in recent]),1) if recent else 0,"completion_rate":round(mean([r["completion_rate"] for r in recent]),1) if recent else 0,"predictability":round(100-mean([abs(r["estimation_variance"])/max(1,r["planned"])*100 for r in recent]),1) if recent else 0,"trends":trends or ["Complete at least two sprints to establish trends."]}
