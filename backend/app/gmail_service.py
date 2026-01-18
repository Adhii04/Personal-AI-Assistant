from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import base64
from datetime import datetime
from typing import List, Dict, Optional


def create_gmail_service(access_token: str):
    """Create Gmail API service with access token"""
    credentials = Credentials(token=access_token)
    return build('gmail', 'v1', credentials=credentials)


def list_emails(access_token: str, max_results: int = 10, query: str = "") -> List[Dict]:
    """
    List emails from user's inbox
    
    Args:
        access_token: Google OAuth access token
        max_results: Number of emails to fetch (default 10, max 100)
        query: Gmail search query (e.g., "is:unread", "from:example@gmail.com")
    
    Returns:
        List of email summaries
    """
    try:
        service = create_gmail_service(access_token)
        
        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
        
        # Fetch details for each message
        email_list = []
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = {header['name']: header['value'] for header in msg['payload']['headers']}
            
            email_list.append({
                'id': msg['id'],
                'thread_id': msg['threadId'],
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'snippet': msg.get('snippet', '')
            })
        
        return email_list
        
    except Exception as e:
        raise Exception(f"Failed to list emails: {str(e)}")


def get_email_details(access_token: str, message_id: str) -> Dict:
    """
    Get full details of a specific email
    
    Args:
        access_token: Google OAuth access token
        message_id: Gmail message ID
    
    Returns:
        Full email details including body
    """
    try:
        service = create_gmail_service(access_token)
        
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        
        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and not body:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', ''),
            'body': body,
            'snippet': message.get('snippet', '')
        }
        
    except Exception as e:
        raise Exception(f"Failed to get email details: {str(e)}")


def search_emails(access_token: str, search_query: str, max_results: int = 10) -> List[Dict]:
    """
    Search emails using Gmail query syntax
    
    Common queries:
    - "is:unread" - Unread emails
    - "from:example@gmail.com" - From specific sender
    - "subject:important" - Subject contains word
    - "has:attachment" - Has attachments
    - "after:2024/01/01" - After specific date
    
    Args:
        access_token: Google OAuth access token
        search_query: Gmail search query
        max_results: Number of results
    
    Returns:
        List of matching emails
    """
    return list_emails(access_token, max_results, search_query)


def send_email(access_token: str, to: str, subject: str, body: str) -> Dict:
    """
    Send an email
    
    Args:
        access_token: Google OAuth access token
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
    
    Returns:
        Sent message details
    """
    try:
        service = create_gmail_service(access_token)
        
        # Create message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            'id': sent_message['id'],
            'thread_id': sent_message['threadId'],
            'status': 'sent'
        }
        
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")


def draft_email_reply(access_token: str, message_id: str, reply_body: str) -> str:
    """
    Create a draft reply to an email
    
    Args:
        access_token: Google OAuth access token
        message_id: Original message ID to reply to
        reply_body: Reply content
    
    Returns:
        Draft ID
    """
    try:
        service = create_gmail_service(access_token)
        
        # Get original message
        original = service.users().messages().get(
            userId='me',
            id=message_id,
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Message-ID']
        ).execute()
        
        headers = {header['name']: header['value'] for header in original['payload']['headers']}
        
        # Create reply
        message = MIMEText(reply_body)
        message['to'] = headers.get('From', '')
        message['subject'] = 'Re: ' + headers.get('Subject', '')
        message['In-Reply-To'] = headers.get('Message-ID', '')
        message['References'] = headers.get('Message-ID', '')
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Create draft
        draft = service.users().drafts().create(
            userId='me',
            body={
                'message': {
                    'raw': raw_message,
                    'threadId': original['threadId']
                }
            }
        ).execute()
        
        return draft['id']
        
    except Exception as e:
        raise Exception(f"Failed to create draft: {str(e)}")