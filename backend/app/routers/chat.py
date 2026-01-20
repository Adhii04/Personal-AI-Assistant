from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, ChatMessage
from app.schemas import ChatRequest, ChatResponse, ChatMessageResponse
from app.dependencies import get_current_user
from app.config import get_settings
from app.agent_tools import AgentTools
from app.agent.graph import build_agent
from app.memory.loader import load_user_memories

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()

# ----------------------------
# Initialize LLM
# ----------------------------
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
# CHAT (LLM ONLY)
# ----------------------------
@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")

    db.add(ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message,
    ))
    db.commit()

    response = llm.invoke([
        SystemMessage(content="You are a helpful personal AI assistant."),
        HumanMessage(content=chat_request.message),
    ])

    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response.content,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "response": response.content,
        "message_id": assistant_msg.id,
    }


# ----------------------------
# CHAT WITH TOOLS + MEMORY
# ----------------------------
@router.post("/message/tools", response_model=ChatResponse)
def send_message_with_tools(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")

    if not current_user.is_google_connected or not current_user.google_access_token:
        raise HTTPException(status_code=403, detail="Please connect your Google account")

    # -------- Run LangGraph Agent --------
    tools = AgentTools(current_user.google_access_token)
    agent = build_agent(tools)

    try:
        state = agent.invoke({
            "message": chat_request.message,
            "intent": None,
            "result": None,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")

    tool_result = state.get("result", "")

    # -------- LOAD MEMORY FROM DB (FIX) --------
    memories = load_user_memories(current_user.id)

    memory_text = ""
    if memories:
        memory_text = "User preferences and memories:\n" + "\n".join(
            f"- {m}" for m in memories
        )

    # -------- Save user message --------
    db.add(ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message,
    ))
    db.commit()

    # -------- Final LLM response --------
    prompt = f"""
User request:
{chat_request.message}

{memory_text}

Tool result:
{tool_result}

Respond clearly and helpfully, using the user's memory when relevant.
"""

    response = llm.invoke([
        SystemMessage(content="You are a helpful personal AI assistant."),
        HumanMessage(content=prompt),
    ])

    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response.content,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "response": response.content,
        "message_id": assistant_msg.id,
    }


# ----------------------------
# CHAT HISTORY
# ----------------------------
@router.get("/history", response_model=list[ChatMessageResponse])
def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
):
    db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).delete()
    db.commit()
