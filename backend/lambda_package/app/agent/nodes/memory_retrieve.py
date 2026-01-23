from app.models import AgentMemory
from app.database import SessionLocal

def retrieve_memory(state: dict) -> dict:
    db = SessionLocal()

    memories = (
        db.query(AgentMemory)
        .filter(AgentMemory.user_id == state["user_id"])
        .order_by(AgentMemory.created_at.desc())
        .limit(5)
        .all()
    )

    db.close()

    state["memories"] = [m.value for m in memories]
    return state
