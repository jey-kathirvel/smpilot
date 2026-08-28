import re
from datetime import date, timedelta
from tests import test_auth as _test_auth  # noqa: F401
from tests.test_backlog import csrf, setup_project


def test_action_requires_approval_before_execution() -> None:
    client=setup_project("actions-owner@example.com")
    item=client.post("/backlog",data={"csrf":csrf(client,"/backlog"),"type":"Story","title":"Unknown effort","description":"","acceptance_criteria":"","priority":"High","story_points":"","status":"Ready","assignee_id":""},follow_redirects=False)
    item_id=item.headers["location"].rsplit("/",1)[-1]; today=date.today()
    client.post("/sprint",data={"csrf":csrf(client,"/sprint"),"name":"Action Sprint","goal":"Act safely","start_date":today.isoformat(),"end_date":(today+timedelta(days=2)).isoformat()})
    sprint_id=re.search(r'action="/sprint/([^/]+)/items"',client.get("/sprint").text).group(1)
    client.post(f"/sprint/{sprint_id}/items",data={"csrf":csrf(client,"/sprint"),"item_ids":item_id}); client.post(f"/sprint/{sprint_id}/start",data={"csrf":csrf(client,"/sprint")})
    assert client.post("/aria/actions/generate",data={"csrf":csrf(client,"/aria/actions")},follow_redirects=False).status_code==303
    page=client.get("/aria/actions").text; action_id=re.search(r'action="/aria/actions/([0-9a-f-]{36})"',page).group(1)
    assert "Suggested" in page and "PAY-1 is unestimated" in page
    assert client.post(f"/aria/actions/{action_id}",data={"csrf":csrf(client,"/aria/actions"),"decision":"Executed","result":"done"}).status_code==400
    assert client.post(f"/aria/actions/{action_id}",data={"csrf":csrf(client,"/aria/actions"),"decision":"Approved"},follow_redirects=False).status_code==303
    assert client.post(f"/aria/actions/{action_id}",data={"csrf":csrf(client,"/aria/actions"),"decision":"Executed","result":"Discussed with team"},follow_redirects=False).status_code==303
    assert "Discussed with team" in client.get("/aria/actions").text
