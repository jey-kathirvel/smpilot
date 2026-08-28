import re
from datetime import date,timedelta
from tests import test_auth as _test_auth # noqa:F401
from tests.test_backlog import csrf,setup_project
def test_review_retro_and_action_flow():
 c=setup_project("retro@example.com");d=date.today();c.post("/sprint",data={"csrf":csrf(c,"/sprint"),"name":"Retro Sprint","goal":"Learn","start_date":d.isoformat(),"end_date":(d+timedelta(days=1)).isoformat()});sid=re.search(r'action="/sprint/([^/]+)/items"',c.get("/sprint").text).group(1)
 assert c.get(f"/sprints/{sid}/review").status_code==200;c.post(f"/sprints/{sid}/retro",data={"csrf":csrf(c,f"/sprints/{sid}/retro"),"category":"Went Well","content":"Fast feedback"});c.post(f"/sprints/{sid}/retro/actions",data={"csrf":csrf(c,f"/sprints/{sid}/retro"),"title":"Keep demos","description":"Demo daily","owner":"Team","due_date":""});page=c.get(f"/sprints/{sid}/retro").text;assert "Fast feedback" in page and "Keep demos" in page
