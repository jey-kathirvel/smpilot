import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PasswordResetToken, User
from app.services.auth import create_password_reset

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)


def override_db():
    with TestingSession() as db:
        yield db


app.dependency_overrides[get_db] = override_db


@pytest.fixture(autouse=True)
def clean_database():
    with TestingSession() as db:
        db.query(PasswordResetToken).delete()
        db.query(User).delete()
        db.commit()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def csrf(client: TestClient, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(r'name="csrf" value="([^"]+)"', response.text)
    assert match
    return match.group(1)


def signup(client: TestClient, email: str = "aria@example.com", password: str = "SecurePass123"):
    return client.post(
        "/signup",
        data={"csrf": csrf(client, "/signup"), "full_name": "Aria Tester", "email": email, "password": password, "confirm_password": password, "mobile": "", "organization_name": "Test Team"},
        follow_redirects=False,
    )


def test_signup_login_logout_and_protected_page(client: TestClient) -> None:
    response = signup(client)
    assert response.status_code == 303
    assert response.headers["location"] == "/today"
    assert client.get("/today").status_code == 200
    profile = client.get("/profile")
    assert "aria@example.com" in profile.text
    response = client.post("/logout", data={"csrf": csrf(client, "/profile")}, follow_redirects=False)
    assert response.status_code == 303
    assert client.get("/today", follow_redirects=False).headers["location"] == "/login"
    response = client.post("/login", data={"csrf": csrf(client, "/login"), "email": "ARIA@example.com", "password": "SecurePass123"}, follow_redirects=False)
    assert response.status_code == 303
    assert client.get("/today").status_code == 200


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    assert signup(client).status_code == 303
    second_client = TestClient(app)
    response = signup(second_client, email="ARIA@example.com")
    assert response.status_code == 400
    assert "already exists" in response.text


def test_csrf_is_required(client: TestClient) -> None:
    response = client.post("/login", data={"csrf": "invalid", "email": "nobody@example.com", "password": "wrong"})
    assert response.status_code == 403


def test_session_cookie_is_http_only_and_same_site(client: TestClient) -> None:
    response = client.get("/login")
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_forgot_password_does_not_disclose_accounts(client: TestClient) -> None:
    token = csrf(client, "/forgot-password")
    missing = client.post("/forgot-password", data={"csrf": token, "email": "missing@example.com"})
    assert missing.status_code == 200
    assert "If that account exists" in missing.text


def test_password_reset_invalidates_existing_session(client: TestClient) -> None:
    assert signup(client).status_code == 303
    with TestingSession() as db:
        user = db.query(User).filter_by(email="aria@example.com").one()
        token = create_password_reset(db, user, 30)
    reset_client = TestClient(app)
    response = reset_client.post(
        f"/reset-password/{token}",
        data={"csrf": csrf(reset_client, f"/reset-password/{token}"), "password": "NewSecurePass456", "confirm_password": "NewSecurePass456"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert client.get("/today", follow_redirects=False).headers["location"] == "/login"
    response = reset_client.post("/login", data={"csrf": csrf(reset_client, "/login"), "email": "aria@example.com", "password": "NewSecurePass456"}, follow_redirects=False)
    assert response.status_code == 303


def test_users_cannot_see_another_profile(client: TestClient) -> None:
    assert signup(client, "first@example.com").status_code == 303
    other = TestClient(app)
    assert signup(other, "second@example.com").status_code == 303
    first_profile = client.get("/profile").text
    second_profile = other.get("/profile").text
    assert "first@example.com" in first_profile and "second@example.com" not in first_profile
    assert "second@example.com" in second_profile and "first@example.com" not in second_profile
