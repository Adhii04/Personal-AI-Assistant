# app/memory/loader.py
from app.models import AgentMemory
from app.database import SessionLocal

def load_user_memories(user_id: int) -> list[str]:
    db = SessionLocal()
    memories = (
        db.query(AgentMemory)
        .filter(AgentMemory.user_id == user_id)
        .order_by(AgentMemory.created_at.desc())
        .all()
    )
    db.close()

    return [m.value for m in memories]
