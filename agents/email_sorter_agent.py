from typing import Dict, Any
from .base_agent import BaseAgent
from utils.gmail_client import GmailClient

class EmailSorterAgent(BaseAgent):
    def __init__(self):
        super().__init__("EmailSorterAgent")
        self.gmail_client = GmailClient()
        
        # Map categories to Gmail labels (can be configured)
        self.label_mapping = {
            "work": "Work",
            "personal": "Personal",
            "promotional": "Promotions",
            "finance": "Finance",
            "travel": "Travel",
            "shopping": "Shopping",
            "social": "Social",
            "news": "News",
            "health": "Health",
            "education": "Education",
            "events": "Events",
            "updates": "Updates",
            "forums": "Forums",
            "legal": "Legal",
            "other": "Other"
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sort emails by applying appropriate labels based on analysis.
        
        Args:
            input_data: Dictionary containing:
                - email_id: Gmail email ID
                - category: Category determined by analyzer
                - confidence: Confidence score (0-1)
        
        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - label: Applied label
                - message: Status message
        """
        try:
            email_id = input_data.get('email_id')
            category = input_data.get('category', 'other')
            confidence = input_data.get('confidence', 0.0)
            
            if not email_id:
                raise ValueError("Email ID is required")
            
            # Only apply labels if confidence is high enough
            if confidence < 0.5:
                self.log(f"Confidence too low ({confidence}) for email {email_id}, skipping")
                return {
                    'success': False,
                    'label': None,
                    'message': f"Confidence too low: {confidence}"
                }
            
            # Get the appropriate label name
            label_name = self.label_mapping.get(category, self.label_mapping['other'])
            
            # Apply the label
            self.log(f"Applying label '{label_name}' to email {email_id}")
            self.gmail_client.apply_label(email_id, label_name)
            
            # Mark as read if needed
            if input_data.get('mark_as_read', False):
                self.log(f"Marking email {email_id} as read")
                self.gmail_client.mark_as_read(email_id)
            
            return {
                'success': True,
                'label': label_name,
                'message': f"Successfully applied label: {label_name}"
            }
            
        except Exception as e:
            self.handle_error(e, f"Failed to sort email {input_data.get('email_id', 'unknown')}")
            return {
                'success': False,
                'label': None,
                'message': f"Error: {str(e)}"
            } 