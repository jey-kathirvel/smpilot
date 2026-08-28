import uuid
from datetime import date,datetime
from sqlalchemy import Date,DateTime,ForeignKey,String,Text,Uuid
from sqlalchemy.orm import Mapped,mapped_column
from app.database import Base
from app.models.user import utcnow
class RetroFeedback(Base):
    __tablename__="retro_feedback"; id:Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4); sprint_id:Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey("sprints.id",ondelete="CASCADE"),index=True); user_id:Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey("users.id",ondelete="CASCADE")); category:Mapped[str]=mapped_column(String(30)); content:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class RetroAction(Base):
    __tablename__="retro_actions"; id:Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4); source_sprint_id:Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey("sprints.id",ondelete="CASCADE"),index=True); title:Mapped[str]=mapped_column(String(240)); description:Mapped[str]=mapped_column(Text); owner:Mapped[str|None]=mapped_column(String(160)); due_date:Mapped[date|None]=mapped_column(Date); status:Mapped[str]=mapped_column(String(30),default="Open"); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
