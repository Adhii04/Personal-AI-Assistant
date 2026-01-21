# app/agent/graph.py (UPDATED)
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
    
    # NEW: Reasoning state
    belief_state: Optional[BeliefState]
    target_date: Optional[str]  # ISO format
    proposed_time: Optional[str]
    conflicts: Optional[List[tuple[TimeConstraint, TimeConstraint]]]
    needs_clarification: bool
    clarification_question: Optional[str]


# ----------------------------
# Intent Detection Node
# ----------------------------

def detect_intent_node(state: AgentState) -> AgentState:
    """Detect intent AND extract temporal context"""
    msg = state["message"].lower()
    
    # Detect intent
    if any(w in msg for w in ["add", "create", "schedule"]) and \
       any(w in msg for w in ["meeting", "event", "appointment"]):
        intent = "CREATE_EVENT"
    elif any(w in msg for w in ["reschedule", "move"]):
        intent = "RESCHEDULE_EVENT"
    elif any(w in msg for w in ["delete", "cancel"]):
        intent = "DELETE_EVENT"
    elif any(w in msg for w in ["calendar", "schedule", "meeting", "event"]):
        intent = "READ_CALENDAR"
    else:
        intent = "CHAT"
    
    # Extract target date for CREATE_EVENT
    target_date = None
    if intent == "CREATE_EVENT":
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
        "needs_clarification": False,
        "clarification_question": None
    }


# ----------------------------
# Reasoning Node (THE KEY INNOVATION)
# ----------------------------

def reason_about_constraints_node(state: AgentState) -> AgentState:
    """
    This is the THINKING layer that makes the agent intelligent.
    
    It:
    1. Analyzes beliefs
    2. Detects conflicts
    3. Proposes times OR asks for clarification
    4. Explains reasoning
    """
    if state["intent"] != "CREATE_EVENT":
        return state  # Skip reasoning for non-scheduling intents
    
    belief_state = state.get("belief_state")
    if not belief_state:
        # No preferences at all - ask user
        return {
            **state,
            "needs_clarification": True,
            "clarification_question": "What time would you like for this meeting?"
        }
    
    target_date = datetime.fromisoformat(state["target_date"]).date()
    
    # Check for conflicts
    conflicts = belief_state.detect_conflicts(target_date)
    
    if conflicts:
        # Build clarification message
        c1, c2 = conflicts[0]  # Show first conflict
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
    
    # No conflicts - try to propose a time
    proposed_time = belief_state.propose_time(target_date)
    
    if not proposed_time:
        # Couldn't find a valid time
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
# Action Node (NOW TRULY AGENTIC)
# ----------------------------

def run_action_node(state: AgentState, tools: AgentTools) -> AgentState:
    """
    Execute action ONLY if reasoning layer approved.
    Always explains the reasoning behind decisions.
    """
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
            r'(?:for|about|regarding)\s+(.+?)(?:\s+tomorrow|\s+today|$)',
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
        result = tools.create_calendar_event(
            title=title,
            date=state["target_date"],
            time=proposed_time,
            duration_hours=1
        )
        
        # Add reasoning explanation
        belief_state = state.get("belief_state")
        if belief_state:
            target_date = datetime.fromisoformat(state["target_date"]).date()
            explanation = belief_state.explain_reasoning(target_date, proposed_time)
            result += f"\n\n💡 {explanation}"
        
        return {**state, "result": result}
    
    elif intent == "READ_CALENDAR":
        return {**state, "result": tools.get_todays_schedule()}
    
    elif intent == "RESCHEDULE_EVENT":
        return {
            **state,
            "result": (
                "⚠️ Rescheduling needs an event reference.\n"
                "Example: 'Reschedule my 11am meeting to 2pm'"
            )
        }
    
    elif intent == "DELETE_EVENT":
        return {
            **state,
            "result": (
                "⚠️ Deleting needs an event reference.\n"
                "Example: 'Cancel the cricket meeting'"
            )
        }
    
    else:
        return {
            **state,
            "result": "I can help with meetings, emails, and schedules. What would you like to do?"
        }


# ----------------------------
# Build Agent Graph
# ----------------------------

def build_agent(tools: AgentTools, belief_state: BeliefState):
    """Build the agent with reasoning capability"""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("reason_about_constraints", reason_about_constraints_node)
    graph.add_node("run_action", lambda state: run_action_node(state, tools))
    
    # Define flow
    graph.set_entry_point("detect_intent")
    graph.add_edge("detect_intent", "reason_about_constraints")
    graph.add_edge("reason_about_constraints", "run_action")
    graph.add_edge("run_action", END)
    
    return graph.compile()