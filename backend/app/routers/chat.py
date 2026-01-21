# app/routers/chat.py (UPDATED /message/tools endpoint)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, ChatMessage
from app.schemas import ChatRequest, ChatResponse, ChatMessageResponse
from app.dependencies import get_current_user
from app.config import get_settings
from app.agent_tools import AgentTools
from app.agent.graph import build_agent
from app.memory.store import store_user_memory
from app.memory.interpreter import build_belief_state

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

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
# CHAT WITH TOOLS + MEMORY + REASONING
# ----------------------------
@router.post("/message/tools", response_model=ChatResponse)
def send_message_with_tools(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enhanced chat endpoint with reasoning capability.
    
    The agent now:
    1. Stores memories
    2. Interprets memories as beliefs
    3. Reasons about conflicts
    4. Asks for clarification when needed
    5. Explains decisions
    """
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    if not current_user.is_google_connected or not current_user.google_access_token:
        raise HTTPException(status_code=403, detail="Please connect your Google account")
    
    # --- 1. Store Memory if Detected ---
    message_lower = chat_request.message.lower()
    memory_keywords = ["prefer", "hate", "like", "don't like", "never", "always", "usually"]
    
    if any(keyword in message_lower for keyword in memory_keywords):
        store_user_memory(user_id=current_user.id, value=chat_request.message)
    
    # --- 2. Build Belief State from ALL Memories ---
    belief_state = build_belief_state(current_user.id)
    
    # --- 3. Run Agent with Reasoning ---
    tools = AgentTools(current_user.google_access_token)
    agent = build_agent(tools, belief_state)
    
    try:
        state = agent.invoke({
            "message": chat_request.message,
            "intent": None,
            "result": None,
            "belief_state": belief_state,
            "target_date": None,
            "proposed_time": None,
            "conflicts": None,
            "needs_clarification": False,
            "clarification_question": None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")
    
    tool_result = state.get("result", "")
    
    # --- 4. Save User Message ---
    db.add(ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message
    ))
    db.commit()
    
    # --- 5. Generate Natural Language Response ---
    # If the agent already provided a good response, use it directly
    if state.get("needs_clarification") or "💡" in tool_result:
        # Agent already formatted a good response
        final_response = tool_result
    else:
        # Let LLM polish the response
        prompt = f"""
User request: {chat_request.message}

Agent result: {tool_result}

Respond naturally and helpfully, acknowledging the action taken.
Keep it brief and conversational.
"""
        
        llm_response = llm.invoke([
            SystemMessage(content="You are a helpful personal AI assistant."),
            HumanMessage(content=prompt)
        ])
        final_response = llm_response.content
    
    # --- 6. Save Assistant Message ---
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=final_response
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    return {
        "response": final_response,
        "message_id": assistant_msg.id
    }


# ----------------------------
# OTHER ENDPOINTS (unchanged)
# ----------------------------

@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simple LLM chat without tools"""
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
