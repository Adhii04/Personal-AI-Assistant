from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User
from app.schemas import (
    CalendarSummary,
    CalendarEvent,
    CalendarEventDetails,
    EventSearchQuery,
    EventsTimeRange,
    CreateEventRequest
)
from app.dependencies import get_current_user
from app.calendar_service import (
    list_calendars,
    get_upcoming_events,
    get_event_details,
    get_today_events,
    get_week_events,
    search_events
)
from datetime import datetime, timedelta

router = APIRouter(prefix="/calendar", tags=["Calendar"])


def check_google_connected(user: User):
    """Check if user has connected Google account"""
    if not user.is_google_connected or not user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google account not connected. Please connect your Google account first."
        )


@router.get("/calendars", response_model=List[CalendarSummary])
def get_calendars(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all calendars accessible to the user
    """
    check_google_connected(current_user)
    
    try:
        calendars = list_calendars(
            access_token=current_user.google_access_token
        )
        return calendars
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendars: {str(e)}"
        )


@router.get("/events", response_model=List[CalendarEvent])
def get_events(
    max_results: int = 10,
    calendar_id: str = 'primary',
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming events from calendar
    
    Parameters:
    - max_results: Number of events (default 10, max 250)
    - calendar_id: Calendar ID (default 'primary')
    """
    check_google_connected(current_user)
    
    try:
        events = get_upcoming_events(
            access_token=current_user.google_access_token,
            max_results=min(max_results, 250),
            calendar_id=calendar_id
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.get("/events/today", response_model=List[CalendarEvent])
def get_todays_events(
    calendar_id: str = 'primary',
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all events for today
    """
    check_google_connected(current_user)
    
    try:
        events = get_today_events(
            access_token=current_user.google_access_token,
            calendar_id=calendar_id
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch today's events: {str(e)}"
        )


@router.get("/events/week", response_model=List[CalendarEvent])
def get_this_weeks_events(
    calendar_id: str = 'primary',
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all events for the next 7 days
    """
    check_google_connected(current_user)
    
    try:
        events = get_week_events(
            access_token=current_user.google_access_token,
            calendar_id=calendar_id
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch week's events: {str(e)}"
        )


@router.get("/events/{event_id}", response_model=CalendarEventDetails)
def get_event(
    event_id: str,
    calendar_id: str = 'primary',
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific event
    """
    check_google_connected(current_user)
    
    try:
        event = get_event_details(
            access_token=current_user.google_access_token,
            event_id=event_id,
            calendar_id=calendar_id
        )
        return event
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event: {str(e)}"
        )


@router.post("/search", response_model=List[CalendarEvent])
def search_calendar_events(
    search_query: EventSearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for events matching a query
    
    Request body:
    {
        "query": "meeting",
        "max_results": 25,
        "calendar_id": "primary"
    }
    """
    check_google_connected(current_user)
    
    try:
        events = search_events(
            access_token=current_user.google_access_token,
            query=search_query.query,
            max_results=search_query.max_results,
            calendar_id=search_query.calendar_id
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search events: {str(e)}"
        )

@router.post("/events/create")
def create_calendar_event(
    event_data: CreateEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new calendar event
    
    Request body:
    {
        "summary": "Meeting Title",
        "start_time": "2026-01-20T11:00:00",
        "end_time": "2026-01-20T12:00:00",
        "description": "Meeting description",
        "location": "Conference Room"
    }
    """
    check_google_connected(current_user)
    
    try:
        from app.calendar_service import create_event
        
        event = create_event(
            access_token=current_user.google_access_token,
            summary=event_data.summary,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            description=event_data.description,
            location=event_data.location,
            calendar_id=event_data.calendar_id
        )
        return {
            "message": "Event created successfully",
            "event": event
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )

@router.post("/events/range", response_model=List[CalendarEvent])
def get_events_in_range(
    time_range: EventsTimeRange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get events within a custom time range
    """
    check_google_connected(current_user)

    try:
        from app.calendar_service import get_events_by_time_range

        events = get_events_by_time_range(
            access_token=current_user.google_access_token,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
            calendar_id=time_range.calendar_id,
            max_results=time_range.max_results
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events in range: {str(e)}"
        )
