from app.models import AgentMemory
from app.database import SessionLocal

def store_memory(state: dict) -> dict:
    """
    Stores extracted memory into the database.
    Expects the following keys in state:
    - extracted_memory (str)
    - user_id (int)
    - memory_type (optional)
    - memory_key (optional)
    - memory_source (optional)
    """

    if "extracted_memory" not in state:
        return state

    mem = AgentMemory(
        user_id=state["user_id"],
        memory_type=state.get("memory_type", "general"),
        key=state.get("memory_key", "auto"),
        value=state["extracted_memory"],
        source=state.get("memory_source", "chat"),
    )

    db = SessionLocal()
    db.add(mem)
    db.commit()
    db.close()

    return state
