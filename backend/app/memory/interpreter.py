# app/memory/interpreter.py
from typing import List
import re
from datetime import datetime, timedelta, date
from app.models import AgentMemory
from app.database import SessionLocal
from app.agent.beliefs import TimeConstraint, BeliefState

def parse_time_constraint(memory: AgentMemory) -> TimeConstraint:
    """Convert raw memory text into structured constraint"""
    text = memory.value.lower()
    
    # Determine scope
    scope = "global"
    scope_date = None
    if "tomorrow" in text:
        scope = "date_specific"
        scope_date = (datetime.now() + timedelta(days=1)).date()
    elif "today" in text:
        scope = "date_specific"
        scope_date = datetime.now().date()
    elif memory.scope_date:
        scope = "date_specific"
        scope_date = datetime.fromisoformat(memory.scope_date).date() if isinstance(memory.scope_date, str) else memory.scope_date
    
    # Determine priority
    if any(word in text for word in ["hate", "never", "don't", "cannot", "can't"]):
        priority = 100  # Hard constraint
    elif scope == "date_specific":
        priority = 50
    else:
        priority = 10  # Soft preference
    
    # Extract time and rule
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text)
    if not time_match:
        # Try 24h format
        time_match = re.search(r'(\d{1,2}):?(\d{2})?', text)
    
    hour = int(time_match.group(1)) if time_match else 18
    minute = int(time_match.group(2)) if time_match and time_match.group(2) else 0
    period = time_match.group(3) if time_match and len(time_match.groups()) >= 3 else None
    
    if period == "pm" and hour < 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0
    
    time_str = f"{hour:02d}:{minute:02d}"
    
    # Determine rule
    if "after" in text and not any(neg in text for neg in ["not after", "no after"]):
        rule = "after"
    elif any(phrase in text for phrase in ["before", "not after", "no later than", "hate meetings after"]):
        rule = "not_after"
    else:
        rule = "after"  # default
    
    return TimeConstraint(
        type="hard_constraint" if priority == 100 else "preference",
        scope=scope,
        scope_date=scope_date,
        rule=rule,
        time=time_str,
        original_text=memory.value,
        priority=priority
    )

def build_belief_state(user_id: int) -> BeliefState:
    """Build structured belief state from raw memories"""
    db = SessionLocal()
    memories = (
        db.query(AgentMemory)
        .filter(AgentMemory.user_id == user_id)
        .order_by(AgentMemory.created_at.desc())
        .all()
    )
    db.close()
    
    constraints = []
    for memory in memories:
        try:
            constraint = parse_time_constraint(memory)
            constraints.append(constraint)
        except Exception as e:
            # Log parsing failure but continue
            print(f"Failed to parse memory: {memory.value} - {e}")
            continue
    
    return BeliefState(constraints=constraints)