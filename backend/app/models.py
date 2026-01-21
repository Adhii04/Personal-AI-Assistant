from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Google OAuth
    google_id = Column(String, unique=True, nullable=True, index=True)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expiry = Column(DateTime(timezone=True), nullable=True)
    is_google_connected = Column(Boolean, default=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="messages")

class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Memory classification
    memory_type = Column(String, default="preference", nullable=False)
    # e.g. "preference", "fact", "constraint"
    
    key = Column(String, default="meeting_time", nullable=False)
    # e.g. "meeting_time", "work_hours", "email_signature"
    
    value = Column(Text, nullable=False)
    # The raw user statement
    
    scope_date = Column(String, nullable=True)
    # ISO date string for date-specific memories, None for global
    
    source = Column(String, default="chat", nullable=False)
    # How this memory was created: "chat", "import", "system"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgentMemory(id={self.id}, user_id={self.user_id}, type={self.memory_type}, value='{self.value[:50]}...')>"
