# app/memory/store.py (FIXED)
from app.models import AgentMemory
from app.database import SessionLocal
from datetime import datetime, timedelta
import re


def should_store_as_memory(message: str) -> bool:
    """
    Determine if a message should be stored as a memory.
    
    Rules:
    - Must contain preference keywords
    - Should NOT be a direct command (schedule, reschedule, etc.)
    - Can be a compound statement if it starts with preference
    """
    message_lower = message.lower()
    
    # Memory keywords
    memory_keywords = ["prefer", "hate", "like", "don't like", "never", "always", "usually", "dislike"]
    
    # Command keywords that indicate this is NOT just a preference
    command_keywords = ["schedule", "create", "add", "book", "reschedule", "move", "cancel", "delete"]
    
    has_memory_keyword = any(keyword in message_lower for keyword in memory_keywords)
    
    # Special case: "I hate X, schedule Y" - extract just the preference part
    if has_memory_keyword and any(cmd in message_lower for cmd in command_keywords):
        # Check if preference comes before command
        memory_pos = min([message_lower.find(kw) for kw in memory_keywords if kw in message_lower])
        command_pos = min([message_lower.find(kw) for kw in command_keywords if kw in message_lower], default=999)
        
        # If memory keyword comes first, it's worth storing
        return memory_pos < command_pos
    
    return has_memory_keyword


def extract_preference_from_message(message: str) -> str:
    """
    Extract just the preference part from a compound message.
    
    Example:
    "I hate meetings after 2pm tomorrow, schedule a meeting tomorrow"
    → "I hate meetings after 2pm tomorrow"
    """
    message_lower = message.lower()
    
    # Find command keywords
    command_keywords = ["schedule", "create", "add", "book"]
    
    for keyword in command_keywords:
        if keyword in message_lower:
            # Split at the command and take the first part
            parts = re.split(f',\\s*{keyword}', message, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts[0].strip()
    
    return message


def store_user_memory(user_id: int, value: str):
    """
    Store a user memory with intelligent date scope detection.
    Only stores if it's actually a preference, not a command.
    """
    if not should_store_as_memory(value):
        return  # Don't store commands
    
    # Extract just the preference part
    preference = extract_preference_from_message(value)
    
    db = SessionLocal()
    
    text = preference.lower()
    scope_date = None
    
    # Detect date-specific context
    if "tomorrow" in text:
        scope_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    elif "today" in text:
        scope_date = datetime.now().date().isoformat()
    
    mem = AgentMemory(
        user_id=user_id,
        memory_type="preference",
        key="meeting_time",
        value=preference,  # Store cleaned preference
        scope_date=scope_date,
        source="chat"
    )
    
    db.add(mem)
    db.commit()
    db.close()


def clear_user_memories(user_id: int):
    """Clear all memories for a user"""
    db = SessionLocal()
    db.query(AgentMemory).filter(AgentMemory.user_id == user_id).delete()
    db.commit()
    db.close()


def get_memory_count(user_id: int) -> int:
    """Get count of stored memories"""
    db = SessionLocal()
    count = db.query(AgentMemory).filter(AgentMemory.user_id == user_id).count()
    db.close()
    return count