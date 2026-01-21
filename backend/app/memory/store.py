# app/memory/store.py (ENHANCED)
from app.models import AgentMemory
from app.database import SessionLocal
from datetime import datetime, timedelta


def store_user_memory(user_id: int, value: str):
    """
    Store a user memory with intelligent date scope detection.
    
    Examples:
    - "I prefer meetings after 6pm" → global, no scope_date
    - "I hate meetings after 2pm tomorrow" → date-specific, scope_date = tomorrow
    """
    db = SessionLocal()
    
    text = value.lower()
    scope_date = None
    
    # Detect date-specific context
    if "tomorrow" in text:
        scope_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    elif "today" in text:
        scope_date = datetime.now().date().isoformat()
    # Could add more: "next week", "monday", specific dates, etc.
    
    mem = AgentMemory(
        user_id=user_id,
        memory_type="preference",
        key="meeting_time",
        value=value,
        scope_date=scope_date,
        source="chat"
    )
    
    db.add(mem)
    db.commit()
    db.close()


def clear_user_memories(user_id: int):
    """Clear all memories for a user (useful for testing/reset)"""
    db = SessionLocal()
    db.query(AgentMemory).filter(AgentMemory.user_id == user_id).delete()
    db.commit()
    db.close()


def get_memory_count(user_id: int) -> int:
    """Get count of stored memories for a user"""
    db = SessionLocal()
    count = db.query(AgentMemory).filter(AgentMemory.user_id == user_id).count()
    db.close()
    return count