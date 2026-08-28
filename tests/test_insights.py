from tests import test_auth as _test_auth # noqa:F401
from tests.test_backlog import setup_project
def test_insights_is_accessible_and_team_focused():
 page=setup_project("insights@example.com").get("/insights");assert page.status_code==200;assert "Aria Insights" in page.text and "employee scoring" in page.text and 'role="img"' in page.text
