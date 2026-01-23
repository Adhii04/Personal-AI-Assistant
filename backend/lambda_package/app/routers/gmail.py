from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User
from app.schemas import (
    EmailSummary,
    EmailDetails,
    EmailSearchQuery,
    SendEmailRequest,
    DraftReplyRequest
)
from app.dependencies import get_current_user
from app.gmail_service import (
    list_emails,
    get_email_details,
    search_emails,
    send_email,
    draft_email_reply
)

router = APIRouter(prefix="/gmail", tags=["Gmail"])


def check_google_connected(user: User):
    """Check if user has connected Google account"""
    if not user.is_google_connected or not user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google account not connected. Please connect your Google account first."
        )


@router.get("/emails", response_model=List[EmailSummary])
def get_emails(
    max_results: int = 10,
    query: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of emails from user's inbox
    
    Query examples:
    - "" (empty) - Recent emails
    - "is:unread" - Unread emails
    - "from:example@gmail.com" - From specific sender
    - "subject:meeting" - Subject contains word
    """
    check_google_connected(current_user)
    
    try:
        emails = list_emails(
            access_token=current_user.google_access_token,
            max_results=min(max_results, 100),  # Cap at 100
            query=query
        )
        return emails
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}"
        )


@router.get("/emails/{message_id}", response_model=EmailDetails)
def get_email(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full details of a specific email including body
    """
    check_google_connected(current_user)
    
    try:
        email = get_email_details(
            access_token=current_user.google_access_token,
            message_id=message_id
        )
        return email
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch email: {str(e)}"
        )


@router.post("/search", response_model=List[EmailSummary])
def search_user_emails(
    search_query: EmailSearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search emails using Gmail query syntax
    
    Example queries in request body:
    {
        "query": "is:unread from:boss@company.com",
        "max_results": 20
    }
    """
    check_google_connected(current_user)
    
    try:
        emails = search_emails(
            access_token=current_user.google_access_token,
            search_query=search_query.query,
            max_results=search_query.max_results
        )
        return emails
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search emails: {str(e)}"
        )


@router.post("/send")
def send_user_email(
    email_request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send an email
    
    Request body:
    {
        "to": "recipient@example.com",
        "subject": "Hello",
        "body": "Email content here"
    }
    """
    check_google_connected(current_user)
    
    try:
        result = send_email(
            access_token=current_user.google_access_token,
            to=email_request.to,
            subject=email_request.subject,
            body=email_request.body
        )
        return {
            "message": "Email sent successfully",
            "email_id": result['id']
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/draft-reply")
def create_draft_reply(
    draft_request: DraftReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a draft reply to an email
    
    Request body:
    {
        "message_id": "abc123...",
        "reply_body": "Thanks for your email..."
    }
    """
    check_google_connected(current_user)
    
    try:
        draft_id = draft_email_reply(
            access_token=current_user.google_access_token,
            message_id=draft_request.message_id,
            reply_body=draft_request.reply_body
        )
        return {
            "message": "Draft created successfully",
            "draft_id": draft_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}"
        )