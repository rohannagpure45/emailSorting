from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from typing import Dict, List, Any
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class GmailClient:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH')
        self.token_path = os.getenv('GMAIL_TOKEN_PATH')
        self.service = self._get_gmail_service()

    def _get_gmail_service(self):
        """Get Gmail service instance with proper authentication."""
        creds = None
        
        # Load token if exists
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.error(f"Error loading token: {str(e)}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)

    def get_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch unread emails from Gmail."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['UNREAD'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                
                # Get email body
                body = ''
                if 'parts' in msg['payload']:
                    for part in msg['payload']['parts']:
                        if part['mimeType'] == 'text/plain':
                            body = part['body'].get('data', '')
                            break
                else:
                    body = msg['payload']['body'].get('data', '')
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'thread_id': message.get('threadId')
                })
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise

    def apply_label(self, message_id: str, label_name: str) -> None:
        """Apply a label to an email."""
        try:
            # First, get or create the label
            labels = self.service.users().labels().list(userId='me').execute()
            label = next((l for l in labels.get('labels', []) if l['name'] == label_name), None)
            
            if not label:
                # Create new label
                label = self.service.users().labels().create(
                    userId='me',
                    body={'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
                ).execute()
            
            # Apply the label
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label['id']]}
            ).execute()
            
        except Exception as e:
            logger.error(f"Error applying label: {str(e)}")
            raise

    def mark_as_read(self, message_id: str) -> None:
        """Mark an email as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            logger.error(f"Error marking email as read: {str(e)}")
            raise 