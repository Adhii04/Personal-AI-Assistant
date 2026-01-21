from typing import Optional
from datetime import datetime, timedelta

from app.gmail_service import (
    list_emails,
    get_email_details,
    search_emails,
)

from app.calendar_service import (
    get_today_events,
    get_week_events,
    get_upcoming_events,
    create_event,
    update_event,
    delete_event,
    get_events_for_date,
)


class AgentTools:
    """
    Tools that the AI agent can use to interact with Gmail and Google Calendar.
    This class is designed to be consumed by a LangGraph / LangChain agent.
    """

    def __init__(self, google_access_token: str):
        self.access_token = google_access_token

    # -------------------------
    # 📧 Gmail Tools
    # -------------------------

    def get_recent_emails(self, count: int = 5) -> str:
        """Get recent emails from inbox."""
        try:
            emails = list_emails(self.access_token, max_results=count)


            if not emails:
                return "No recent emails found."

            result = f"Found {len(emails)} recent emails:\n\n"
            for i, email in enumerate(emails, 1):
                result += (
                    f"{i}. From: {email['from']}\n"
                    f"   Subject: {email['subject']}\n"
                    f"   Date: {email['date']}\n"
                    f"   Preview: {email['snippet'][:100]}...\n\n"
                )

            return result

        except Exception as e:
            return f"❌ Error fetching emails: {str(e)}"

    def search_emails_by_query(self, query: str, count: int = 5) -> str:
        """Search emails using Gmail query syntax."""
        try:
            emails = search_emails(self.access_token, query, count)

            if not emails:
                return f"No emails found matching query: {query}"

            result = f"Found {len(emails)} emails matching '{query}':\n\n"
            for i, email in enumerate(emails, 1):
                result += (
                    f"{i}. From: {email['from']}\n"
                    f"   Subject: {email['subject']}\n"
                    f"   Date: {email['date']}\n"
                    f"   Preview: {email['snippet'][:100]}...\n\n"
                )

            return result

        except Exception as e:
            return f"❌ Error searching emails: {str(e)}"

    def get_email_content(self, message_id: str) -> str:
        """Get full content of a specific email."""
        try:
            email = get_email_details(self.access_token, message_id)

            return (
                "📧 Email Details:\n\n"
                f"From: {email['from']}\n"
                f"To: {email['to']}\n"
                f"Subject: {email['subject']}\n"
                f"Date: {email['date']}\n\n"
                f"Body:\n{email['body'][:1000]}"
            )

        except Exception as e:
            return f"❌ Error fetching email content: {str(e)}"

    # -------------------------
    # 📅 Calendar Tools
    # -------------------------

    def get_todays_schedule(self) -> str:
        """Get today's calendar events."""
        try:
            today = datetime.now().date().isoformat()
            return self.get_schedule_for_date(today)

        except Exception as e:
            return f"❌ Error fetching today's schedule: {str(e)}"

    def get_upcoming_schedule(self, days: int = 7) -> str:
        """Get upcoming calendar events."""
        try:
            if days == 7:
                events = get_week_events(self.access_token)
            else:
                events = get_upcoming_events(self.access_token, max_results=50)

            if not events:
                return f"No events scheduled for the next {days} days."

            result = f"📅 Upcoming Schedule ({len(events)} events):\n\n"
            for i, event in enumerate(events, 1):
                result += (
                    f"{i}. {event['summary']}\n"
                    f"   Time: {event['start']}\n"
                )
                if event.get("location"):
                    result += f"   Location: {event['location']}\n"
                result += "\n"

            return result

        except Exception as e:
            return f"❌ Error fetching upcoming schedule: {str(e)}"

    def get_schedule_for_date(self, date: str) -> str:
        """Get all calendar events for a specific date (YYYY-MM-DD)."""
        try:
            events = get_events_for_date(self.access_token, date)

            if not events:
                return "No events scheduled for this day."

            formatted = []
            for event in events:
                start = event["start"]
                title = event.get("summary", "Untitled Event")

                if "T" in start:
                    time_obj = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    time_str = time_obj.strftime("%I:%M %p")
                    formatted.append(f"• {time_str} - {title}")
                else:
                    formatted.append(f"• All day - {title}")

            return "\n".join(formatted)

        except Exception as e:
            return f"❌ Error fetching schedule: {str(e)}"

    def check_availability(self, time_description: str) -> str:
        """
        Approximate availability check.
        NOTE: Does not yet parse natural language time.
        """
        try:
            events = get_today_events(self.access_token)

            if not events:
                return f"✅ You appear to be free {time_description}."

            result = (
                "⚠️ Availability check is approximate.\n"
                "Here are today's events:\n\n"
            )

            for event in events:
                result += f"- {event['summary']} at {event['start']}\n"

            return result

        except Exception as e:
            return f"❌ Error checking availability: {str(e)}"

    def create_calendar_event(
        self,
        title: str,
        date: str,
        time: str,
        duration_hours: int = 1,
    ) -> str:
        """Create a calendar event."""
        try:
            start = datetime.fromisoformat(f"{date}T{time}:00")
            end = start + timedelta(hours=duration_hours)

            event = create_event(
                access_token=self.access_token,
                summary=title,
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )

            return (
                "✅ Event created successfully!\n"
                f"Title: {title}\n"
                f"Time: {start.strftime('%B %d, %Y at %I:%M %p')}\n"
                f"Link: {event['html_link']}"
            )

        except Exception as e:
            return f"❌ Failed to create event: {str(e)}"

    def reschedule_meeting(
        self,
        event_id: str,
        new_date: str,
        new_time: str,
        duration_hours: int = 1,
    ) -> str:
        """Reschedule an existing calendar event."""
        try:
            start = datetime.fromisoformat(f"{new_date}T{new_time}:00")
            end = start + timedelta(hours=duration_hours)

            event = update_event(
                access_token=self.access_token,
                event_id=event_id,
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )

            return (
                "✅ Meeting rescheduled successfully\n"
                f"Title: {event['summary']}\n"
                f"New Time: {start.strftime('%I:%M %p')}\n"
                f"Link: {event['html_link']}"
            )

        except Exception as e:
            return f"❌ Failed to reschedule meeting: {str(e)}"

    def delete_meeting(self, event_id: str) -> str:
        """Delete a calendar event."""
        try:
            delete_event(self.access_token, event_id)
            return "✅ Meeting deleted successfully."

        except Exception as e:
            return f"❌ Failed to delete meeting: {str(e)}"


# -------------------------
# 🧠 Tool Description (for LLM)
# -------------------------

def get_available_tools_description() -> str:
    return """
You are a personal AI assistant with access to the user's Gmail and Google Calendar.

Available Tools:
1. get_recent_emails(count)
2. search_emails_by_query(query, count)
3. get_email_content(message_id)
4. get_todays_schedule()
5. get_upcoming_schedule(days)
6. get_schedule_for_date(date)
7. check_availability(time)
8. create_calendar_event(title, date, time, duration)
9. reschedule_meeting(event_id, new_date, new_time)
10. delete_meeting(event_id)

Guidelines:
- Use tools to fetch real data
- Summarize clearly
- Suggest actions
- Respect user privacy
"""
