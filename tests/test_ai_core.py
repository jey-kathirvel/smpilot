import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.context import build_project_context
from app.ai.schemas import AriaResponse
from app.ai.service import AriaService
from app.config import Settings
from app.database import Base
from app.models import AIAuditLog, Project, User, Workspace, WorkspaceMember

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)


class SuccessfulClient:
    def structured(self, **kwargs):
        return kwargs["schema"](summary="Sprint context reviewed", health="ON_TRACK", confidence=0.9, recommendations=["Keep focus"])


class FailingClient:
    def structured(self, **kwargs):
        raise RuntimeError("provider unavailable")


def fallback():
    return AriaResponse(summary="AI unavailable; deterministic metrics remain available.", health="UNKNOWN", confidence=1.0)


def create_project(db, suffix: str) -> Project:
    user = User(full_name="Owner", email=f"{suffix}-{uuid.uuid4()}@example.com", password_hash="test")
    db.add(user); db.flush()
    workspace = Workspace(name=f"Workspace {suffix}", owner_user_id=user.id, timezone="UTC")
    db.add(workspace); db.flush(); db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="Admin"))
    project = Project(workspace_id=workspace.id, name=f"Project {suffix}", project_key=suffix[:8].upper(), status="Active")
    db.add(project); db.commit(); return project


def test_structured_response_is_audited() -> None:
    with Session() as db:
        project = create_project(db, "core")
        service = AriaService(Settings(openai_api_key="test-key", _env_file=None), client=SuccessfulClient())
        result = service.run(db, feature="core_test", project_id=project.id, sprint_id=None, prompt_version="test-v1", context=build_project_context(db, project), schema=AriaResponse, fallback=fallback)
        assert result.health == "ON_TRACK"
        audit = db.scalar(select(AIAuditLog).where(AIAuditLog.project_id == project.id, AIAuditLog.feature == "core_test"))
        assert audit.status == "SUCCESS" and len(audit.request_context_hash) == 64


def test_provider_failure_uses_validated_fallback() -> None:
    with Session() as db:
        project = create_project(db, "fallback")
        service = AriaService(Settings(openai_api_key="test-key", _env_file=None), client=FailingClient())
        result = service.run(db, feature="failure_test", project_id=project.id, sprint_id=None, prompt_version="test-v1", context=build_project_context(db, project), schema=AriaResponse, fallback=fallback)
        assert result.health == "UNKNOWN"
        assert db.scalar(select(AIAuditLog).where(AIAuditLog.project_id == project.id, AIAuditLog.feature == "failure_test")).status == "FAILED_FALLBACK"


def test_context_never_includes_another_project() -> None:
    with Session() as db:
        first, second = create_project(db, "first"), create_project(db, "second")
        context = build_project_context(db, first)
        assert context["project"]["id"] == str(first.id)
        assert context["project"]["id"] != str(second.id)


def test_openrouter_free_is_the_default_ai_route() -> None:
    settings = Settings(_env_file=None)
    assert settings.ai_provider == "openrouter"
    assert settings.ai_model == "openrouter/free"
    assert settings.ai_base_url == "https://openrouter.ai/api/v1"
