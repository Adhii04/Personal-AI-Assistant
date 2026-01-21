# app/memory/interpreter.py
"""
Memory Interpreter: Converts raw memory strings into structured beliefs.
This is where string matching happens - not in the agent logic.
"""

from typing import List
import re
from datetime import datetime, timedelta, date
from app.models import AgentMemory
from app.database import SessionLocal
from app.agent.beliefs import TimeConstraint, BeliefState


def parse_time_constraint(memory: AgentMemory) -> TimeConstraint:
    """
    Convert a raw memory string into a structured TimeConstraint.
    
    Examples:
    - "I prefer meetings after 6pm" → after 18:00, priority 10
    - "I hate meetings after 2pm tomorrow" → not_after 14:00, priority 100
    - "No meetings after 11pm" → not_after 23:00, priority 100
    """
    text = memory.value.lower()
    
    # --- 1. Determine Scope (global vs date-specific) ---
    scope = "global"
    scope_date = None
    
    if "tomorrow" in text:
        scope = "date_specific"
        # Use scope_date from memory if available
        if memory.scope_date:
            scope_date = datetime.fromisoformat(memory.scope_date).date() if isinstance(memory.scope_date, str) else memory.scope_date
        else:
            scope_date = (datetime.now() + timedelta(days=1)).date()
    elif "today" in text:
        scope = "date_specific"
        scope_date = datetime.now().date()
    elif memory.scope_date:
        scope = "date_specific"
        scope_date = datetime.fromisoformat(memory.scope_date).date() if isinstance(memory.scope_date, str) else memory.scope_date
    
    # --- 2. Determine Priority (hard constraint vs preference) ---
    hard_constraint_keywords = ["hate", "never", "don't", "do not", "cannot", "can't", "no meetings"]
    is_hard_constraint = any(word in text for word in hard_constraint_keywords)
    
    if is_hard_constraint:
        priority = 100
        constraint_type = "hard_constraint"
    elif scope == "date_specific":
        priority = 50
        constraint_type = "preference"
    else:
        priority = 10
        constraint_type = "preference"
    
    # --- 3. Extract Time ---
    time_str = "18:00"  # default
    
    # Try to find time in various formats
    # Format: "6pm", "6:30pm", "18:00"
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)
        
        # Convert to 24-hour format
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        
        time_str = f"{hour:02d}:{minute:02d}"
    
    # --- 4. Determine Rule (after, before, not_after, not_before) ---
    rule = "after"  # default
    
    if any(phrase in text for phrase in ["hate meeting after", "hate meetings after", "no meetings after", "not after", "no later than"]):
        rule = "not_after"
    elif any(phrase in text for phrase in ["before", "earlier than"]):
        rule = "not_after"  # "before X" means "not after X"
    elif "after" in text and not any(neg in text for neg in ["not after", "no after"]):
        rule = "after"
    elif any(phrase in text for phrase in ["prefer", "like"]) and "after" in text:
        rule = "after"
    
    return TimeConstraint(
        type=constraint_type,
        scope=scope,
        scope_date=scope_date,
        rule=rule,
        time=time_str,
        original_text=memory.value,
        priority=priority
    )


def build_belief_state(user_id: int) -> BeliefState:
    """
    Build a complete belief state from all user memories.
    This is called every time the agent needs to make a decision.
    """
    db = SessionLocal()
    try:
        memories = (
            db.query(AgentMemory)
            .filter(AgentMemory.user_id == user_id)
            .order_by(AgentMemory.created_at.desc())
            .all()
        )
    finally:
        db.close()
    
    constraints = []
    for memory in memories:
        try:
            constraint = parse_time_constraint(memory)
            constraints.append(constraint)
        except Exception as e:
            # Log parsing failure but continue
            print(f"⚠️ Failed to parse memory: {memory.value} - {e}")
            continue
    
    return BeliefState(constraints=constraints)


def get_constraints_for_date(user_id: int, target_date: date) -> List[TimeConstraint]:
    """
    Convenience function to get all active constraints for a specific date.
    """
    belief_state = build_belief_state(user_id)
    return belief_state.get_active_constraints(target_date)