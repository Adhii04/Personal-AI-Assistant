from typing import List, Dict, Optional
from app.gmail_service import list_emails, get_email_details, search_emails
from app.calendar_service import get_upcoming_events, get_today_events, get_week_events


class AgentTools:
    """Tools that the AI agent can use to interact with Gmail and Calendar"""
    
    def __init__(self, google_access_token: str):
        self.access_token = google_access_token
    
    def get_recent_emails(self, count: int = 5) -> str:
        """
        Get recent emails from inbox
        Returns formatted string with email summaries
        """
        try:
            emails = list_emails(self.access_token, max_results=count)
            
            if not emails:
                return "No recent emails found."
            
            result = f"Found {len(emails)} recent emails:\n\n"
            for i, email in enumerate(emails, 1):
                result += f"{i}. From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                result += f"   Preview: {email['snippet'][:100]}...\n\n"
            
            return result
        except Exception as e:
            return f"Error fetching emails: {str(e)}"
    
    def search_emails_by_query(self, query: str, count: int = 5) -> str:
        """
        Search emails using Gmail query syntax
        Examples: "is:unread", "from:boss@company.com", "subject:meeting"
        """
        try:
            emails = search_emails(self.access_token, query, count)
            
            if not emails:
                return f"No emails found matching query: {query}"
            
            result = f"Found {len(emails)} emails matching '{query}':\n\n"
            for i, email in enumerate(emails, 1):
                result += f"{i}. From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                result += f"   Preview: {email['snippet'][:100]}...\n\n"
            
            return result
        except Exception as e:
            return f"Error searching emails: {str(e)}"
    
    def get_email_content(self, message_id: str) -> str:
        """
        Get full content of a specific email
        """
        try:
            email = get_email_details(self.access_token, message_id)
            
            result = f"Email Details:\n\n"
            result += f"From: {email['from']}\n"
            result += f"To: {email['to']}\n"
            result += f"Subject: {email['subject']}\n"
            result += f"Date: {email['date']}\n\n"
            result += f"Body:\n{email['body'][:1000]}"  # Limit to 1000 chars
            
            return result
        except Exception as e:
            return f"Error fetching email content: {str(e)}"
    
    def get_todays_schedule(self) -> str:
        """
        Get all events scheduled for today
        """
        try:
            events = get_today_events(self.access_token)
            
            if not events:
                return "No events scheduled for today."
            
            result = f"Today's Schedule ({len(events)} events):\n\n"
            for i, event in enumerate(events, 1):
                result += f"{i}. {event['summary']}\n"
                result += f"   Time: {event['start']} to {event['end']}\n"
                if event['location']:
                    result += f"   Location: {event['location']}\n"
                if event['attendees']:
                    result += f"   Attendees: {', '.join(event['attendees'][:3])}\n"
                result += "\n"
            
            return result
        except Exception as e:
            return f"Error fetching today's schedule: {str(e)}"
    
    def get_upcoming_schedule(self, days: int = 7) -> str:
        """
        Get events for the next N days
        """
        try:
            if days == 7:
                events = get_week_events(self.access_token)
            else:
                events = get_upcoming_events(self.access_token, max_results=50)
            
            if not events:
                return f"No events scheduled for the next {days} days."
            
            result = f"Upcoming Schedule ({len(events)} events):\n\n"
            for i, event in enumerate(events, 1):
                result += f"{i}. {event['summary']}\n"
                result += f"   Time: {event['start']}\n"
                if event['location']:
                    result += f"   Location: {event['location']}\n"
                result += "\n"
            
            return result
        except Exception as e:
            return f"Error fetching upcoming schedule: {str(e)}"
    
    def check_availability(self, time_description: str) -> str:
        """
        Check if user is available at a given time
        Note: This is a simple implementation - real impl would parse time_description
        """
        try:
            events = get_today_events(self.access_token)
            
            if not events:
                return f"You appear to be free {time_description}. No events found."
            
            result = f"Checking availability {time_description}...\n\n"
            result += f"You have {len(events)} events today:\n"
            for event in events:
                result += f"- {event['summary']} at {event['start']}\n"
            
            return result
        except Exception as e:
            return f"Error checking availability: {str(e)}"


def get_available_tools_description() -> str:
    """
    Returns a description of available tools for the AI agent
    """
    return """
You are a personal AI assistant with access to the user's Gmail and Google Calendar.

Available Tools:
1. get_recent_emails(count) - Get recent emails from inbox
2. search_emails_by_query(query, count) - Search emails (e.g., "is:unread", "from:boss@company.com")
3. get_email_content(message_id) - Get full content of specific email
4. get_todays_schedule() - Get all events for today
5. get_upcoming_schedule(days) - Get events for next N days
6. check_availability(time) - Check if user is available

Guidelines:
- Be proactive: If user asks about emails or schedule, use the tools to fetch real data
- Be specific: Use actual email subjects, senders, and event details
- Be helpful: Suggest actions based on what you find
- Be concise: Summarize information clearly
- Respect privacy: Don't share sensitive info unnecessarily

Examples:
User: "What's in my inbox?"
→ Use get_recent_emails(5) and summarize the emails

User: "Do I have any meetings today?"
→ Use get_todays_schedule() and list the meetings

User: "Any emails from my boss?"
→ Use search_emails_by_query("from:boss@company.com", 5)
"""