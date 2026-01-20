from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import re

from app.database import get_db
from app.models import User, ChatMessage
from app.schemas import ChatRequest, ChatResponse, ChatMessageResponse
from app.dependencies import get_current_user
from app.config import get_settings
from app.agent_tools import AgentTools

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()

# Initialize LLM
if settings.openai_api_key:
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
    )
else:
    llm = None


# ----------------------------
# Helpers
# ----------------------------

def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(w in msg for w in ["add", "create", "schedule"]) and \
       any(w in msg for w in ["meeting", "event", "appointment"]):
        return "CREATE_EVENT"

    if any(w in msg for w in ["reschedule", "move"]):
        return "RESCHEDULE_EVENT"

    if any(w in msg for w in ["delete", "cancel"]):
        return "DELETE_EVENT"

    if any(w in msg for w in ["schedule", "calendar", "meeting", "event"]):
        return "READ_CALENDAR"

    return "CHAT"


def extract_time_and_title(message: str):
    """
    Extract time (11am / 3:30pm) and title (for cricket match)
    """
    msg = message.lower()

    # Time
    time_match = re.search(r'\b(1[0-2]|0?[1-9])(?::([0-5][0-9]))?\s*(am|pm)\b', msg)
    if not time_match:
        return None, None

    hour = int(time_match.group(1))
    minute = int(time_match.group(2)) if time_match.group(2) else 0
    period = time_match.group(3)

    if period == "pm" and hour < 12:
        hour += 12
    if period == "am" and hour == 12:
        hour = 0

    time_str = f"{hour:02d}:{minute:02d}"

    # Title
    title = "Meeting"
    title_match = re.search(r'for\s+(.+)', message, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    return time_str, title


# ----------------------------
# Chat (LLM only)
# ----------------------------

@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")

    user_msg = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_msg)
    db.commit()

    messages = [
        SystemMessage(content="You are a helpful personal AI assistant."),
        HumanMessage(content=chat_request.message)
    ]

    response = llm.invoke(messages)

    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response.content
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "response": response.content,
        "message_id": assistant_msg.id
    }


# ----------------------------
# Chat WITH TOOLS (Agent)
# ----------------------------

@router.post("/message/tools", response_model=ChatResponse)
def send_message_with_tools(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")

    if not current_user.is_google_connected or not current_user.google_access_token:
        raise HTTPException(
            status_code=403,
            detail="Please connect your Google account"
        )

    tools = AgentTools(current_user.google_access_token)
    intent = detect_intent(chat_request.message)
    tool_result = None

    # ----------------------------
    # INTENT EXECUTION
    # ----------------------------

    if intent == "CREATE_EVENT":
        time_str, title = extract_time_and_title(chat_request.message)

        if not time_str:
            tool_result = "❌ I couldn't understand the time. Try: 'Add meeting at 11am'"
        else:
            today = datetime.now()
            tool_result = tools.create_calendar_event(
                title=title,
                date=today.strftime("%Y-%m-%d"),
                time=time_str,
                duration_hours=1
            )

    elif intent == "READ_CALENDAR":
        tool_result = tools.get_todays_schedule()

    elif intent == "RESCHEDULE_EVENT":
        tool_result = (
            "⚠️ Rescheduling is supported, but I need the event reference.\n"
            "Example: 'Reschedule my 11am meeting to 2pm'"
        )

    elif intent == "DELETE_EVENT":
        tool_result = (
            "⚠️ Deleting is supported, but I need the event reference.\n"
            "Example: 'Cancel the cricket meeting'"
        )

    else:
        tool_result = "I can help with meetings, emails, and schedules."

    # ----------------------------
    # SAVE USER MESSAGE
    # ----------------------------

    db.add(ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message
    ))
    db.commit()

    # ----------------------------
    # LLM SUMMARY
    # ----------------------------

    prompt = f"""
User request:
{chat_request.message}

Tool result:
{tool_result}

Respond clearly and helpfully.
"""

    response = llm.invoke([
        SystemMessage(content="You are a helpful personal assistant."),
        HumanMessage(content=prompt)
    ])

    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response.content
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "response": response.content,
        "message_id": assistant_msg.id
    }


# ----------------------------
# Chat History
# ----------------------------

@router.get("/history", response_model=list[ChatMessageResponse])
def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


@router.delete("/history", status_code=204)
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).delete()
    db.commit()
