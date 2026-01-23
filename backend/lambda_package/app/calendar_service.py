from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def create_calendar_service(access_token: str):
    """Create Google Calendar API service with access token"""
    credentials = Credentials(token=access_token)
    return build('calendar', 'v3', credentials=credentials)


def list_calendars(access_token: str) -> List[Dict]:
    """
    List all calendars accessible to the user
    
    Args:
        access_token: Google OAuth access token
    
    Returns:
        List of calendar summaries
    """
    try:
        service = create_calendar_service(access_token)
        
        calendar_list = service.calendarList().list().execute()
        
        calendars = []
        for calendar in calendar_list.get('items', []):
            calendars.append({
                'id': calendar['id'],
                'summary': calendar.get('summary', ''),
                'description': calendar.get('description', ''),
                'primary': calendar.get('primary', False),
                'timezone': calendar.get('timeZone', '')
            })
        
        return calendars
        
    except Exception as e:
        raise Exception(f"Failed to list calendars: {str(e)}")


def get_upcoming_events(
    access_token: str,
    max_results: int = 10,
    calendar_id: str = 'primary',
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None
) -> List[Dict]:
    """
    Get upcoming events from calendar
    
    Args:
        access_token: Google OAuth access token
        max_results: Number of events to fetch (default 10, max 250)
        calendar_id: Calendar ID (default 'primary')
        time_min: Start time (default: now)
        time_max: End time (default: None)
    
    Returns:
        List of calendar events
    """
    try:
        service = create_calendar_service(access_token)
        
        # Default to current time if not specified
        if time_min is None:
            time_min = datetime.utcnow()
        
        # Format times in RFC3339 format
        time_min_str = time_min.isoformat() + 'Z'
        time_max_str = time_max.isoformat() + 'Z' if time_max else None
        
        # Build request parameters
        params = {
            'calendarId': calendar_id,
            'timeMin': time_min_str,
            'maxResults': min(max_results, 250),
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        if time_max_str:
            params['timeMax'] = time_max_str
        
        # Fetch events
        events_result = service.events().list(**params).execute()
        events = events_result.get('items', [])
        
        # Format events
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'attendees': [
                    attendee.get('email') 
                    for attendee in event.get('attendees', [])
                ],
                'organizer': event.get('organizer', {}).get('email', ''),
                'status': event.get('status', ''),
                'html_link': event.get('htmlLink', '')
            })
        
        return formatted_events
        
    except Exception as e:
        raise Exception(f"Failed to get events: {str(e)}")


def get_event_details(access_token: str, event_id: str, calendar_id: str = 'primary') -> Dict:
    """
    Get detailed information about a specific event
    
    Args:
        access_token: Google OAuth access token
        event_id: Event ID
        calendar_id: Calendar ID (default 'primary')
    
    Returns:
        Event details
    """
    try:
        service = create_calendar_service(access_token)
        
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        return {
            'id': event['id'],
            'summary': event.get('summary', 'No title'),
            'description': event.get('description', ''),
            'start': start,
            'end': end,
            'location': event.get('location', ''),
            'attendees': [
                {
                    'email': attendee.get('email'),
                    'response_status': attendee.get('responseStatus')
                }
                for attendee in event.get('attendees', [])
            ],
            'organizer': event.get('organizer', {}),
            'status': event.get('status', ''),
            'html_link': event.get('htmlLink', ''),
            'created': event.get('created', ''),
            'updated': event.get('updated', '')
        }
        
    except Exception as e:
        raise Exception(f"Failed to get event details: {str(e)}")


def get_today_events(access_token: str, calendar_id: str = 'primary') -> List[Dict]:
    """
    Get all events for today
    
    Args:
        access_token: Google OAuth access token
        calendar_id: Calendar ID (default 'primary')
    
    Returns:
        List of today's events
    """
    # Get today's date range
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    return get_upcoming_events(
        access_token=access_token,
        max_results=50,
        calendar_id=calendar_id,
        time_min=start_of_day,
        time_max=end_of_day
    )


def get_week_events(access_token: str, calendar_id: str = 'primary') -> List[Dict]:
    """
    Get all events for the next 7 days
    
    Args:
        access_token: Google OAuth access token
        calendar_id: Calendar ID (default 'primary')
    
    Returns:
        List of this week's events
    """
    now = datetime.utcnow()
    one_week_later = now + timedelta(days=7)
    
    return get_upcoming_events(
        access_token=access_token,
        max_results=100,
        calendar_id=calendar_id,
        time_min=now,
        time_max=one_week_later
    )


def search_events(
    access_token: str,
    query: str,
    max_results: int = 25,
    calendar_id: str = 'primary'
) -> List[Dict]:
    """
    Search for events matching a query
    
    Args:
        access_token: Google OAuth access token
        query: Search query (searches summary, description, location, attendees)
        max_results: Number of results
        calendar_id: Calendar ID (default 'primary')
    
    Returns:
        List of matching events
    """
    try:
        service = create_calendar_service(access_token)
        
        events_result = service.events().list(
            calendarId=calendar_id,
            q=query,
            maxResults=min(max_results, 250),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'attendees': [
                    attendee.get('email') 
                    for attendee in event.get('attendees', [])
                ],
                'organizer': event.get('organizer', {}).get('email', ''),
                'html_link': event.get('htmlLink', '')
            })
        
        return formatted_events
        
    except Exception as e:
        raise Exception(f"Failed to search events: {str(e)}")
    
def create_event(
    access_token: str,
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    calendar_id: str = 'primary'
    ) -> Dict:
        """
        Create a new calendar event
        
        Args:
            access_token: Google OAuth access token
            summary: Event title
            start_time: Start time in ISO format (e.g., "2026-01-20T11:00:00")
            end_time: End time in ISO format
            description: Event description
            location: Event location
            calendar_id: Calendar ID (default 'primary')
        
        Returns:
            Created event details
        """
        try:
            service = create_calendar_service(access_token)
            
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
            }
            
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            return {
                'id': created_event['id'],
                'summary': created_event.get('summary', ''),
                'start': created_event['start'].get('dateTime', ''),
                'end': created_event['end'].get('dateTime', ''),
                'html_link': created_event.get('htmlLink', ''),
                'status': 'created'
            }
            
        except Exception as e:
            raise Exception(f"Failed to create event: {str(e)}")
        
def update_event(
    access_token: str,
    event_id: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary"
    ) -> Dict:
        try:
            service = create_calendar_service(access_token)

            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            event["start"]["dateTime"] = start_time
            event["end"]["dateTime"] = end_time

            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            return {
                "id": updated_event["id"],
                "summary": updated_event.get("summary", ""),
                "start": updated_event["start"]["dateTime"],
                "end": updated_event["end"]["dateTime"],
                "html_link": updated_event.get("htmlLink", "")
            }

        except Exception as e:
            raise Exception(f"Failed to reschedule event: {str(e)}")

def delete_event(
    access_token: str,
    event_id: str,
    calendar_id: str = "primary"
    ) -> str:
        try:
            service = create_calendar_service(access_token)

            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return "Event deleted successfully"

        except Exception as e:
            raise Exception(f"Failed to delete event: {str(e)}")

def get_events_for_date(access_token: str, date: str):
    """
    Fetch all calendar events for a specific date (YYYY-MM-DD)
    """
    creds = Credentials(token=access_token)
    service = build("calendar", "v3", credentials=creds)

    target_date = datetime.fromisoformat(date)

    time_min = target_date.replace(
        hour=0, minute=0, second=0
    ).isoformat() + "Z"

    time_max = target_date.replace(
        hour=23, minute=59, second=59
    ).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    formatted = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        formatted.append({
            "summary": event.get("summary", "Untitled Event"),
            "start": start,
        })

    return formatted