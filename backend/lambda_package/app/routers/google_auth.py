from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User
from app.schemas import GoogleAuthURL, GoogleAuthCallback, GoogleConnectionStatus, Token
from app.dependencies import get_current_user
from app.auth import create_access_token
from app.google_auth import (
    get_authorization_url,
    exchange_code_for_tokens,
    get_user_info
)
from app.config import get_settings
from datetime import timedelta

router = APIRouter(prefix="/google", tags=["Google OAuth"])
settings = get_settings()


@router.get("/auth-url", response_model=GoogleAuthURL)
def get_google_auth_url():
    """
    Get Google OAuth authorization URL
    Frontend redirects user to this URL to start OAuth flow
    """
    auth_url, state = get_authorization_url()
    return {"auth_url": auth_url}


@router.post("/callback", response_model=Token)
def google_oauth_callback(
    callback_data: GoogleAuthCallback,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    Exchange authorization code for tokens and create/login user
    """
    try:
        # Exchange code for tokens
        tokens = exchange_code_for_tokens(callback_data.code)
        
        # Get user info from Google
        user_info = get_user_info(tokens['access_token'])
        
        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info['google_id']).first()
        
        if not user:
            # Check if email exists (user registered with email/password)
            user = db.query(User).filter(User.email == user_info['email']).first()
            
            if user:
                # Link Google account to existing user
                user.google_id = user_info['google_id']
            else:
                # Create new user
                user = User(
                    email=user_info['email'],
                    google_id=user_info['google_id']
                )
                db.add(user)
        
        # Update Google tokens
        user.google_access_token = tokens['access_token']
        user.google_refresh_token = tokens['refresh_token']
        user.google_token_expiry = tokens['token_expiry']
        user.is_google_connected = True
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token for our app
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )


@router.post("/connect")
def connect_google_account(
    callback_data: GoogleAuthCallback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect Google account to existing logged-in user
    """
    try:
        # Exchange code for tokens
        tokens = exchange_code_for_tokens(callback_data.code)
        
        # Get user info from Google
        user_info = get_user_info(tokens['access_token'])
        
        # Update current user with Google credentials
        current_user.google_id = user_info['google_id']
        current_user.google_access_token = tokens['access_token']
        current_user.google_refresh_token = tokens['refresh_token']
        current_user.google_token_expiry = tokens['token_expiry']
        current_user.is_google_connected = True
        
        db.commit()
        
        return {
            "message": "Google account connected successfully",
            "email": user_info['email']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Google account: {str(e)}"
        )


@router.post("/disconnect")
def disconnect_google_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Google account from user
    """
    current_user.google_access_token = None
    current_user.google_refresh_token = None
    current_user.google_token_expiry = None
    current_user.is_google_connected = False
    
    db.commit()
    
    return {"message": "Google account disconnected successfully"}


@router.get("/status", response_model=GoogleConnectionStatus)
def get_google_connection_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has connected their Google account
    """
    return {
        "is_connected": current_user.is_google_connected,
        "email": current_user.email if current_user.is_google_connected else None,
        "connected_at": current_user.google_token_expiry
    }