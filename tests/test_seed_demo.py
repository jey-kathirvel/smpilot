from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import AriaAction, Project, Sprint, TeamMember, WorkItem, WorkItemDependency
from scripts.seed_demo import seed_demo


def test_demo_seed_is_realistic_and_idempotent():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = seed_demo(db, "demo-seed@example.com", "SecureDemoPass123")
        second = seed_demo(db, "demo-seed@example.com", "SecureDemoPass123")
        assert first.id == second.id
        assert first.name == "Payment Platform Modernization"
        assert db.scalar(select(func.count()).select_from(Project)) == 1
        assert db.scalar(select(func.count()).select_from(TeamMember)) == 5
        assert db.scalar(select(func.count()).select_from(WorkItem)) == 10
        assert db.scalar(select(func.count()).select_from(WorkItemDependency)) == 1
        assert db.scalar(select(func.count()).select_from(Sprint).where(Sprint.status == "Completed")) == 3
        assert db.scalar(select(func.count()).select_from(Sprint).where(Sprint.status == "Active")) == 1
        assert db.scalar(select(func.count()).select_from(AriaAction)) == 2
