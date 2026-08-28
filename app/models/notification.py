import uuid
from datetime import datetime
from sqlalchemy import Boolean,DateTime,ForeignKey,String,Uuid
from sqlalchemy.orm import Mapped,mapped_column
from app.database import Base
from app.models.user import utcnow
class Notification(Base):
 __tablename__="notifications";id:Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4);project_id:Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey("projects.id",ondelete="CASCADE"),index=True);user_id:Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey("users.id",ondelete="CASCADE"),index=True);type:Mapped[str]=mapped_column(String(60));title:Mapped[str]=mapped_column(String(240));body:Mapped[str]=mapped_column(String(1200));read:Mapped[bool]=mapped_column(Boolean,default=False);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
