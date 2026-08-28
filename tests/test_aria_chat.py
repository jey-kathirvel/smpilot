from app.config import Settings
from tests import test_auth as _test_auth # noqa:F401
from tests.test_backlog import csrf,setup_project
def test_ask_aria_is_grounded_when_sprint_missing(monkeypatch):
    monkeypatch.setattr("app.routers.aria_chat.get_settings",lambda:Settings(openrouter_api_key="",_env_file=None)); client=setup_project("chat@example.com")
    response=client.post("/aria",data={"csrf":csrf(client,"/aria"),"question":"Can we finish this sprint?"},follow_redirects=False)
    assert response.status_code==303; page=client.get("/aria").text
    assert "There is no active sprint" in page and "No active sprint" in page
