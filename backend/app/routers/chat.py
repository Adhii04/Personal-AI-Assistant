from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ChatMessage
from app.schemas import ChatRequest, ChatResponse, ChatMessageResponse
from app.dependencies import get_current_user
from app.config import get_settings
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()

# Initialize LangChain LLM
if settings.openai_api_key:
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url
    )
else:
    llm = None


@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    # Save user message
    user_message = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    
    # Get recent chat history (last 10 messages)
    recent_messages = db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(10)\
        .all()
    
    # Build conversation context
    messages = [
        SystemMessage(content="You are a helpful personal assistant. Be concise and friendly.")
    ]
    
    # Add history in chronological order
    for msg in reversed(recent_messages[:-1]):  # Exclude the message we just added
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    
    # Add current message
    messages.append(HumanMessage(content=chat_request.message))
    
    # Get LLM response
    try:
        response = llm.invoke(messages)
        assistant_content = response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    # Save assistant message
    assistant_message = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=assistant_content
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return {
        "response": assistant_content,
        "message_id": assistant_message.id
    }


@router.get("/history", response_model=list[ChatMessageResponse])
def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(limit)\
        .all()
    
    return list(reversed(messages))


@router.delete("/history", status_code=204)
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .delete()
    db.commit()
    
    return None
