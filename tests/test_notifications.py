from tests import test_auth as _test_auth # noqa:F401
from tests.test_backlog import setup_project
def test_notification_center_and_count():
 c=setup_project("notify@example.com");assert c.get("/notifications").status_code==200;assert c.get("/notifications/unread-count").json()=={"count":0};assert "Mark all read" in c.get("/notifications").text
