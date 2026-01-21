# app/memory/interpreter.py (FIXED)
from typing import List
import re
from datetime import datetime, timedelta, date
from app.models import AgentMemory
from app.database import SessionLocal
from app.agent.beliefs import TimeConstraint, BeliefState


def parse_time_constraint(memory: AgentMemory) -> TimeConstraint:
    """
    Convert a raw memory string into a structured TimeConstraint.
    
    Fixed to handle:
    - "hate meetings after 2pm" → not_after 14:00
    - "hate meetings after 2 tomorrow" → not_after 14:00 (assumes pm for single digit)
    """
    text = memory.value.lower()
    
    # --- 1. Determine Scope ---
    scope = "global"
    scope_date = None
    
    if "tomorrow" in text:
        scope = "date_specific"
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
    
    # --- 2. Determine Priority ---
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
    
    # --- 3. Extract Time (IMPROVED) ---
    time_str = "18:00"  # default
    
    # Pattern 1: "6pm", "6:30pm", "18:00"
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)
        
        # If no am/pm specified and hour is small (1-12), assume context
        if not period:
            # "after 2" in afternoon context → assume pm
            # "after 6" in evening context → could be pm
            # For safety, if hour < 8 and no period, assume pm
            if hour < 8:
                period = "pm"
            # If hour >= 8 and <= 12, it's ambiguous but likely pm in work context
            elif 8 <= hour <= 12:
                period = "pm"
        
        # Convert to 24-hour format
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        
        time_str = f"{hour:02d}:{minute:02d}"
    
    # --- 4. Determine Rule ---
    rule = "after"  # default
    
    # "hate meetings after X" means "not_after X"
    if any(phrase in text for phrase in ["hate meeting after", "hate meetings after", "no meetings after"]):
        rule = "not_after"
    elif any(phrase in text for phrase in ["not after", "no later than"]):
        rule = "not_after"
    elif any(phrase in text for phrase in ["before", "earlier than"]):
        rule = "not_after"
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
    """Build a complete belief state from all user memories"""
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
            print(f"⚠️ Failed to parse memory: {memory.value} - {e}")
            continue
    
    return BeliefState(constraints=constraints)


def get_constraints_for_date(user_id: int, target_date: date) -> List[TimeConstraint]:
    """Get all active constraints for a specific date"""
    belief_state = build_belief_state(user_id)
    return belief_state.get_active_constraints(target_date)