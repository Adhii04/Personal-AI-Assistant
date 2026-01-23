# app/agent/graph.py (FIXED)
from typing import TypedDict, Optional, List
from datetime import datetime, timedelta
import re

from langgraph.graph import StateGraph, END
from app.agent_tools import AgentTools
from app.agent.beliefs import BeliefState, TimeConstraint


# ----------------------------
# Enhanced Agent State
# ----------------------------

class AgentState(TypedDict):
    message: str
    intent: Optional[str]
    result: Optional[str]
    
    # Reasoning state
    belief_state: Optional[BeliefState]
    target_date: Optional[str]
    proposed_time: Optional[str]
    conflicts: Optional[List[tuple[TimeConstraint, TimeConstraint]]]
    needs_clarification: bool
    clarification_question: Optional[str]
    user_override_time: Optional[str]  # NEW: User explicitly specified time


# ----------------------------
# Intent Detection Node
# ----------------------------

def detect_intent_node(state: AgentState) -> AgentState:
    """Detect intent AND extract temporal context"""
    msg = state["message"].lower()
    
    # Detect intent with better logic
    intent = "CHAT"
    
    # Priority 1: Reading/viewing intents (check first)
    if any(phrase in msg for phrase in ["what's my", "what is my", "show my", "list my", "view my", "get my", "check my", "tell me what"]):
        intent = "READ_CALENDAR"
    elif any(phrase in msg for phrase in ["do i have", "any meetings", "my schedule", "my calendar"]) and \
         not any(w in msg for w in ["schedule a", "create a", "add a"]):
        intent = "READ_CALENDAR"
    # Priority 2: Modification intents
    elif any(w in msg for w in ["reschedule", "move", "change"]) and any(w in msg for w in ["meeting", "event"]):
        intent = "RESCHEDULE_EVENT"
    elif any(w in msg for w in ["delete", "cancel", "remove"]) and any(w in msg for w in ["meeting", "event"]):
        intent = "DELETE_EVENT"
    # Priority 3: Creation intents
    elif any(phrase in msg for phrase in ["schedule a", "schedule the", "create a", "create the", "add a", "add the", "book a", "book the"]):
        intent = "CREATE_EVENT"
    elif any(phrase in msg for phrase in ["schedule meeting", "create meeting", "add meeting", "book meeting"]):
        intent = "CREATE_EVENT"
    
    # Extract target date for CREATE_EVENT
    target_date = None
    user_override_time = None
    
    if intent == "CREATE_EVENT":
        if "tomorrow" in msg:
            target_date = (datetime.now() + timedelta(days=1)).date().isoformat()
        elif "today" in msg:
            target_date = datetime.now().date().isoformat()
        else:
            target_date = datetime.now().date().isoformat()
        
        # Check if user specified a time explicitly (overrides preferences)
        time_patterns = [
            r'(?:before|by)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
            r'(?:at|for)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, msg)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
                
                if period == "pm" and hour < 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                
                # If "before X", schedule 1 hour before
                if "before" in msg or "by" in msg:
                    hour = max(9, hour - 1)
                
                user_override_time = f"{hour:02d}:{minute:02d}"
                break
    
    elif intent == "READ_CALENDAR":
        # Extract what timeframe they're asking about
        if "tomorrow" in msg:
            target_date = (datetime.now() + timedelta(days=1)).date().isoformat()
        elif "today" in msg:
            target_date = datetime.now().date().isoformat()
        else:
            target_date = datetime.now().date().isoformat()  # default to today
    
    return {
        **state,
        "intent": intent,
        "target_date": target_date,
        "user_override_time": user_override_time,
        "needs_clarification": False,
        "clarification_question": None
    }


# ----------------------------
# Reasoning Node
# ----------------------------

def reason_about_constraints_node(state: AgentState) -> AgentState:
    """
    This is the THINKING layer.
    Handles user overrides and conflict detection.
    """
    if state["intent"] != "CREATE_EVENT":
        return state
    
    # If user explicitly specified a time, use it (no reasoning needed)
    if state.get("user_override_time"):
        return {
            **state,
            "proposed_time": state["user_override_time"],
            "needs_clarification": False
        }
    
    belief_state = state.get("belief_state")
    if not belief_state:
        return {
            **state,
            "needs_clarification": True,
            "clarification_question": "What time would you like for this meeting?"
        }
    
    target_date = datetime.fromisoformat(state["target_date"]).date()
    
    # Check for conflicts
    conflicts = belief_state.detect_conflicts(target_date)
    
    if conflicts:
        c1, c2 = conflicts[0]
        question = (
            f"🤔 I found conflicting preferences:\n\n"
            f"• \"{c1.original_text}\"\n"
            f"• \"{c2.original_text}\"\n\n"
            f"Which should I prioritize for {target_date.strftime('%B %d')}?"
        )
        return {
            **state,
            "needs_clarification": True,
            "clarification_question": question,
            "conflicts": conflicts
        }
    
    # No conflicts - propose a time
    proposed_time = belief_state.propose_time(target_date)
    
    if not proposed_time:
        active_constraints = belief_state.get_active_constraints(target_date)
        constraint_text = "\n".join(f"• {c.original_text}" for c in active_constraints[:3])
        return {
            **state,
            "needs_clarification": True,
            "clarification_question": (
                f"I'm having trouble finding a time that satisfies:\n{constraint_text}\n\n"
                f"What time would work best?"
            )
        }
    
    return {
        **state,
        "proposed_time": proposed_time,
        "needs_clarification": False
    }


# ----------------------------
# Action Node
# ----------------------------

def run_action_node(state: AgentState, tools: AgentTools) -> AgentState:
    """Execute action with proper error handling"""
    intent = state["intent"]
    message = state["message"]
    
    # Handle clarification path
    if state.get("needs_clarification"):
        return {
            **state,
            "result": state["clarification_question"]
        }
    
    if intent == "CREATE_EVENT":
        # Extract meeting title
        title_match = re.search(
            r'(?:meeting|event)(?:\s+for|\s+about|\s+regarding)?\s+(.+?)(?:\s+tomorrow|\s+today|\s+at|\s+before|\s+after|$)',
            message,
            re.IGNORECASE
        )
        title = title_match.group(1).strip() if title_match else "Meeting"
        
        proposed_time = state.get("proposed_time")
        if not proposed_time:
            return {
                **state,
                "result": "❌ I couldn't determine a suitable time for this meeting."
            }
        
        # Execute the action
        try:
            result = tools.create_calendar_event(
                title=title,
                date=state["target_date"],
                time=proposed_time,
                duration_hours=1
            )
            
            # Add reasoning explanation (only if not user override)
            if not state.get("user_override_time"):
                belief_state = state.get("belief_state")
                if belief_state:
                    target_date = datetime.fromisoformat(state["target_date"]).date()
                    explanation = belief_state.explain_reasoning(target_date, proposed_time)
                    result += f"\n\n💡 {explanation}"
            
            return {**state, "result": result}
        except Exception as e:
            return {**state, "result": f"❌ Failed to create event: {str(e)}"}
    
    elif intent == "READ_CALENDAR":
        try:
            target_date = datetime.fromisoformat(state["target_date"]).date()
            
            # Get schedule for the requested date
            schedule = tools.get_schedule_for_date(target_date.isoformat())
            
            # Format the response nicely
            if not schedule or "No events" in schedule:
                date_str = "today" if target_date == datetime.now().date() else "tomorrow"
                result = f"📅 You have no meetings scheduled for {date_str}."
            else:
                date_str = "Today" if target_date == datetime.now().date() else "Tomorrow"
                result = f"📅 {date_str}'s schedule:\n\n{schedule}"
            
            return {**state, "result": result}
        except Exception as e:
            return {**state, "result": f"❌ Failed to fetch schedule: {str(e)}"}
    
    elif intent == "RESCHEDULE_EVENT":
        return {
            **state,
            "result": (
                "⚠️ To reschedule, I need to know:\n"
                "1. Which meeting to reschedule (e.g., 'the 11am meeting' or 'cricket meeting')\n"
                "2. What time to move it to\n\n"
                "Example: 'Reschedule my 11am meeting to 2pm'"
            )
        }
    
    elif intent == "DELETE_EVENT":
        return {
            **state,
            "result": (
                "⚠️ To cancel, I need to know which meeting.\n"
                "Example: 'Cancel the cricket meeting' or 'Delete my 2pm meeting'"
            )
        }
    
    else:
        return {
            **state,
            "result": "I can help with scheduling meetings, viewing your calendar, and managing events. What would you like to do?"
        }


# ----------------------------
# Build Agent Graph
# ----------------------------

def build_agent(tools: AgentTools, belief_state: BeliefState):
    """Build the agent with reasoning capability"""
    graph = StateGraph(AgentState)
    
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("reason_about_constraints", reason_about_constraints_node)
    graph.add_node("run_action", lambda state: run_action_node(state, tools))
    
    graph.set_entry_point("detect_intent")
    graph.add_edge("detect_intent", "reason_about_constraints")
    graph.add_edge("reason_about_constraints", "run_action")
    graph.add_edge("run_action", END)
    
    return graph.compile()