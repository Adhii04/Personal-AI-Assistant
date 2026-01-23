from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import datetime
from typing import Optional, List


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v) > 72:
            raise ValueError('Password cannot be longer than 72 characters')
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Chat Schemas
class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    response: str
    message_id: int

class GoogleAuthURL(BaseModel):
    auth_url: str


class GoogleAuthCallback(BaseModel):
    code: str


class GoogleConnectionStatus(BaseModel):
    is_connected: bool
    email: Optional[str] = None
    connected_at: Optional[datetime] = None


class GoogleTokens(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None

# Gmail Schemas
class EmailSummary(BaseModel):
    id: str
    thread_id: str
    from_: str = Field(alias="from")
    to: str
    subject: str
    date: str
    snippet: str
    
    class Config:
        populate_by_name = True


class EmailDetails(BaseModel):
    id: str
    thread_id: str
    from_: str = Field(alias="from")
    to: str
    subject: str
    date: str
    body: str
    snippet: str
    
    class Config:
        populate_by_name = True


class EmailSearchQuery(BaseModel):
    query: str
    max_results: int = 10


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class DraftReplyRequest(BaseModel):
    message_id: str
    reply_body: str

# Calendar Schemas
class CalendarSummary(BaseModel):
    id: str
    summary: str
    description: str
    primary: bool
    timezone: str


class EventAttendee(BaseModel):
    email: str
    response_status: Optional[str] = None


class CalendarEvent(BaseModel):
    id: str
    summary: str
    description: str
    start: str
    end: str
    location: str
    attendees: List[str]
    organizer: str
    status: str
    html_link: str


class CalendarEventDetails(BaseModel):
    id: str
    summary: str
    description: str
    start: str
    end: str
    location: str
    attendees: List[EventAttendee]
    organizer: dict
    status: str
    html_link: str
    created: str
    updated: str


class EventSearchQuery(BaseModel):
    query: str
    max_results: int = 25
    calendar_id: str = 'primary'


class EventsTimeRange(BaseModel):
    calendar_id: str = 'primary'
    max_results: int = 10

class CreateEventRequest(BaseModel):
    summary: str
    start_time: str
    end_time: str
    description: str = ""
    location: str = ""
    calendar_id: str = 'primary'