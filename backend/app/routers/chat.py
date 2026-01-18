from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ChatMessage
from app.schemas import ChatRequest, ChatResponse, ChatMessageResponse
from app.dependencies import get_current_user
from app.config import get_settings
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.agent_tools import AgentTools, get_available_tools_description
import json
import re

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


def execute_agent_tool(tools: AgentTools, tool_call: str) -> str:
    """
    Execute an agent tool based on the tool call string
    """
    try:
        # Parse tool call (format: "function_name(args)")
        match = re.match(r'(\w+)\((.*?)\)', tool_call)
        if not match:
            return f"Invalid tool call format: {tool_call}"
        
        function_name = match.group(1)
        args_str = match.group(2)
        
        # Parse arguments
        args = []
        if args_str:
            # Simple argument parsing (handles strings and numbers)
            for arg in args_str.split(','):
                arg = arg.strip().strip('"').strip("'")
                try:
                    # Try to convert to int
                    args.append(int(arg))
                except ValueError:
                    args.append(arg)
        
        # Execute tool
        if hasattr(tools, function_name):
            tool_function = getattr(tools, function_name)
            result = tool_function(*args)
            return result
        else:
            return f"Tool not found: {function_name}"
            
    except Exception as e:
        return f"Error executing tool: {str(e)}"


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
    
    # Get recent chat history
    recent_messages = db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(10)\
        .all()
    
    # Check if user has Google connected
    has_google_access = current_user.is_google_connected and current_user.google_access_token
    
    # Build system message
    if has_google_access:
        system_content = f"""You are a helpful personal AI assistant with access to the user's Gmail and Google Calendar.

{get_available_tools_description()}

When the user asks about emails or calendar, you should:
1. Tell them you're checking their Gmail/Calendar
2. Indicate which tool you would use (e.g., "Let me check your recent emails...")
3. Provide a natural, helpful response

Note: In this simplified version, describe what you would do. Full tool integration coming soon.
"""
    else:
        system_content = "You are a helpful personal assistant. Be concise and friendly. Note: User hasn't connected their Google account yet, so you can't access their emails or calendar."
    
    # Build conversation context
    messages = [SystemMessage(content=system_content)]
    
    # Add history
    for msg in reversed(recent_messages[:-1]):
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
        
        # If user has Google access and message is about emails/calendar, add helpful note
        if has_google_access:
            email_keywords = ['email', 'inbox', 'mail', 'message']
            calendar_keywords = ['calendar', 'schedule', 'meeting', 'event', 'appointment']
            
            user_message_lower = chat_request.message.lower()
            
            if any(keyword in user_message_lower for keyword in email_keywords):
                assistant_content += "\n\n💡 Tip: I can access your Gmail! Try asking me to 'check my recent emails' or 'search for emails from [person]'."
            elif any(keyword in user_message_lower for keyword in calendar_keywords):
                assistant_content += "\n\n💡 Tip: I can access your Calendar! Try asking me 'what's on my schedule today?' or 'do I have any meetings this week?'."
        
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


@router.post("/message/tools", response_model=ChatResponse)
def send_message_with_tools(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced chat endpoint that actually executes Gmail/Calendar tools
    """
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    # Check if user has Google access
    if not current_user.is_google_connected or not current_user.google_access_token:
        raise HTTPException(
            status_code=403,
            detail="Please connect your Google account to use this feature"
        )
    
    # Initialize agent tools
    tools = AgentTools(current_user.google_access_token)
    
    # Determine which tool to use based on user message
    message_lower = chat_request.message.lower()
    tool_result = None
    
    if 'recent email' in message_lower or 'inbox' in message_lower:
        tool_result = tools.get_recent_emails(5)
    elif 'unread email' in message_lower:
        tool_result = tools.search_emails_by_query('is:unread', 5)
    elif 'today' in message_lower and ('schedule' in message_lower or 'meeting' in message_lower or 'event' in message_lower):
        tool_result = tools.get_todays_schedule()
    elif 'this week' in message_lower or 'upcoming' in message_lower:
        tool_result = tools.get_upcoming_schedule(7)
    
    # Save user message
    user_message = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    
    # Build prompt with tool result
    if tool_result:
        enhanced_prompt = f"User question: {chat_request.message}\n\nData from user's Gmail/Calendar:\n{tool_result}\n\nPlease provide a helpful summary and answer based on this information."
    else:
        enhanced_prompt = chat_request.message
    
    # Get LLM response
    messages = [
        SystemMessage(content="You are a helpful personal assistant. Summarize the data clearly and provide actionable insights."),
        HumanMessage(content=enhanced_prompt)
    ]
    
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