from typing import TypedDict, Optional
from datetime import datetime
import re

from langgraph.graph import StateGraph
from app.agent_tools import AgentTools
from langgraph.graph import END



# ----------------------------
# Agent State
# ----------------------------

class AgentState(TypedDict):
    message: str
    intent: Optional[str]
    result: Optional[str]


# ----------------------------
# Intent Detection Node
# ----------------------------

def detect_intent_node(state: AgentState) -> AgentState:
    msg = state["message"].lower()

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

    return {
        **state,
        "intent": intent
    }


# ----------------------------
# Helper: extract time & title
# ----------------------------

def extract_time_and_title(message: str):
    time_match = re.search(
        r'\b(1[0-2]|0?[1-9])(?::([0-5][0-9]))?\s*(am|pm)\b',
        message.lower()
    )

    if not time_match:
        return None, "Meeting"

    hour = int(time_match.group(1))
    minute = int(time_match.group(2)) if time_match.group(2) else 0
    period = time_match.group(3)

    if period == "pm" and hour < 12:
        hour += 12
    if period == "am" and hour == 12:
        hour = 0

    time_str = f"{hour:02d}:{minute:02d}"

    title = "Meeting"
    title_match = re.search(r'for\s+(.+)', message, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    return time_str, title


# ----------------------------
# Action Node
# ----------------------------

def run_action_node(state: AgentState, tools: AgentTools) -> AgentState:
    intent = state["intent"]
    message = state["message"]

    if intent == "CREATE_EVENT":
        time_str, title = extract_time_and_title(message)

        if not time_str:
            result = "❌ I couldn't understand the time. Try: 'Add meeting at 11am'"
        else:
            today = datetime.now()
            result = tools.create_calendar_event(
                title=title,
                date=today.strftime("%Y-%m-%d"),
                time=time_str,
                duration_hours=1
            )

    elif intent == "READ_CALENDAR":
        result = tools.get_todays_schedule()

    elif intent == "RESCHEDULE_EVENT":
        result = (
            "⚠️ Rescheduling needs an event reference.\n"
            "Example: 'Reschedule my 11am meeting to 2pm'"
        )

    elif intent == "DELETE_EVENT":
        result = (
            "⚠️ Deleting needs an event reference.\n"
            "Example: 'Cancel the cricket meeting'"
        )

    else:
        result = "I can help with meetings, emails, and schedules."

    return {
        **state,
        "result": result
    }


# ----------------------------
# Build LangGraph Agent
# ----------------------------

def build_agent(tools: AgentTools):
    graph = StateGraph(AgentState)

    # ✅ Node names must NOT collide with state keys
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("run_action", lambda state: run_action_node(state, tools))

    graph.set_entry_point("detect_intent")
    graph.add_edge("detect_intent", "run_action")
    graph.add_edge("run_action", END)


    return graph.compile()
