from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ai import AriaAction
from app.models.organization import TeamMember
from app.models.standup import DailyStandup
from app.models.sprint import Sprint
from app.services.risks import sprint_risks
def meeting_recommendation(db:Session,project_id,sprint:Sprint|None,day:date|None=None)->dict:
    today=day or date.today(); members=db.scalars(select(TeamMember).where(TeamMember.project_id==project_id,TeamMember.active.is_(True))).all(); submitted=set(db.scalars(select(DailyStandup.user_id).where(DailyStandup.project_id==project_id,DailyStandup.update_date==today)).all()); missing=[m.display_name for m in members if m.user_id and m.user_id not in submitted]
    risks=sprint_risks(db,sprint) if sprint else []; critical=[r for r in risks if r["level"]=="HIGH"]; actions=db.scalars(select(AriaAction).where(AriaAction.project_id==project_id,AriaAction.status.in_(["Suggested","Approved"]))).all(); topics=[r["title"] for r in critical[:3]]+[a.title for a in actions[:2]]
    if not critical and not topics and not missing: return {"outcome":"No Scrum Meeting Needed","duration":0,"participants":[],"topics":[],"rationale":["All team members updated","No new critical blockers","No unresolved actions"]}
    return {"outcome":"Focused Sync Recommended","duration":10,"participants":["Product Owner","Relevant owners"],"topics":topics or ["Missing stand-up updates"],"rationale":[f"{len(critical)} critical risk(s)",f"{len(missing)} missing update(s)",f"{len(actions)} unresolved action(s)"]}
