# app/models.py or wherever AgentMemory is defined
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base

class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # ADDED MISSING COLUMNS
    memory_type = Column(String, default="preference", nullable=False)
    key = Column(String, default="meeting_time", nullable=False)
    value = Column(Text, nullable=False)  # Changed to Text for longer content
    scope_date = Column(String, nullable=True)  # ISO date string or None
    source = Column(String, default="chat", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())