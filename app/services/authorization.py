import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.organization import Project, Workspace, WorkspaceMember
from app.models.user import User


def authorized_workspaces(db: Session, user: User):
    return db.scalars(select(Workspace).outerjoin(WorkspaceMember).where(or_(Workspace.owner_user_id == user.id, WorkspaceMember.user_id == user.id)).distinct()).all()


def get_workspace(db: Session, user: User, workspace_id: str | uuid.UUID | None) -> Workspace | None:
    if not workspace_id:
        return None
    try:
        value = uuid.UUID(str(workspace_id))
    except ValueError:
        return None
    return db.scalar(select(Workspace).outerjoin(WorkspaceMember).where(Workspace.id == value, or_(Workspace.owner_user_id == user.id, WorkspaceMember.user_id == user.id)))


def get_project(db: Session, user: User, project_id: str | uuid.UUID | None) -> Project | None:
    if not project_id:
        return None
    try:
        value = uuid.UUID(str(project_id))
    except ValueError:
        return None
    return db.scalar(select(Project).join(Workspace).outerjoin(WorkspaceMember).where(Project.id == value, or_(Workspace.owner_user_id == user.id, WorkspaceMember.user_id == user.id)))
