from app.database import SessionLocal
from app.models import AgentMemory

def store_user_memory(user_id: int, value: str):
    db = SessionLocal()
    memory = AgentMemory(
        user_id=user_id,
        value=value
    )
    db.add(memory)
    db.commit()
    db.close()
