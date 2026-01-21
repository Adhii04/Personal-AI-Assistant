from app.models import AgentMemory
from app.database import SessionLocal
from datetime import datetime, timedelta

def store_user_memory(user_id: int, value: str):
    db = SessionLocal()
    
    text = value.lower()
    scope_date = None
    
    # Better date parsing
    if "tomorrow" in text:
        scope_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    elif "today" in text:
        scope_date = datetime.now().date().isoformat()
    
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
