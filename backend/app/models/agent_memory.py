from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    value = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
