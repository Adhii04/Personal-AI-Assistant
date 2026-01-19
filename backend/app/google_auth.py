from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from datetime import datetime, timedelta
from app.config import get_settings
import os

settings = get_settings()

# OAuth 2.0 scopes
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
]


def create_oauth_flow():
    """Create OAuth flow for Google authentication"""
    # For development, disable HTTPS requirement
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri]
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri
    )
    
    return flow


def get_authorization_url():
    """Generate Google OAuth authorization URL"""
    flow = create_oauth_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )
    return auth_url, state


def exchange_code_for_tokens(code: str):
    """Exchange authorization code for access tokens"""
    flow = create_oauth_flow()
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    
    return {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_expiry': credentials.expiry,
        'scopes': credentials.scopes
    }


def get_user_info(access_token: str):
    """Get user info from Google"""
    credentials = Credentials(token=access_token)
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    
    return {
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture'),
        'google_id': user_info.get('id')
    }


def refresh_access_token(refresh_token: str):
    """Refresh access token using refresh token"""
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret
    )
    
    credentials.refresh(Request())
    
    return {
        'access_token': credentials.token,
        'token_expiry': credentials.expiry
    }


def create_gmail_service(access_token: str):
    """Create Gmail API service"""
    credentials = Credentials(token=access_token)
    return build('gmail', 'v1', credentials=credentials)


def create_calendar_service(access_token: str):
    """Create Calendar API service"""
    credentials = Credentials(token=access_token)
    return build('calendar', 'v3', credentials=credentials)
