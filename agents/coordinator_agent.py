from typing import Dict, Any, List
from .base_agent import BaseAgent
from .email_analyzer_agent import EmailAnalyzerAgent
from .email_sorter_agent import EmailSorterAgent
from utils.gmail_client import GmailClient
from loguru import logger
import json
import os
from datetime import datetime

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.analyzer = EmailAnalyzerAgent()
        self.sorter = EmailSorterAgent()
        self.gmail_client = GmailClient()
        
        # Configuration options
        self.batch_size = 10  # Number of emails to process at once
        self.confidence_threshold = 0.5  # Minimum confidence to apply sorting
        self.auto_mark_as_read = True  # Whether to mark processed emails as read
        self.save_analysis = True  # Whether to save detailed analysis results
        
        # Create analysis results directory
        os.makedirs("analysis_results", exist_ok=True)
        
    async def process(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Coordinate the email analysis and sorting workflow.
        
        Args:
            input_data: Optional dictionary with configuration overrides
                - batch_size: Override default batch size
                - confidence_threshold: Override default confidence threshold
                - auto_mark_as_read: Override auto mark as read setting
                - save_analysis: Override saving detailed analysis
        
        Returns:
            Dictionary containing summary of processed emails
        """
        try:
            # Apply any configuration overrides
            if input_data:
                self.batch_size = input_data.get('batch_size', self.batch_size)
                self.confidence_threshold = input_data.get('confidence_threshold', self.confidence_threshold)
                self.auto_mark_as_read = input_data.get('auto_mark_as_read', self.auto_mark_as_read)
                self.save_analysis = input_data.get('save_analysis', self.save_analysis)
            
            self.log(f"Starting email processing with batch size: {self.batch_size}")
            
            # Fetch unread emails
            emails = self.gmail_client.get_unread_emails(max_results=self.batch_size)
            
            if not emails:
                self.log("No unread emails found")
                return {'processed': 0, 'results': []}
            
            results = []
            
            # Process each email
            for email in emails:
                email_id = email['id']
                subject = email['subject']
                
                self.log(f"Processing email: {subject}")
                
                # Step 1: Analyze email
                analysis = await self.analyzer.process(email)
                
                # Apply priority-based processing
                priority_result = self._handle_priority(email_id, analysis)
                
                # Step 2: Sort email based on analysis
                sorter_input = {
                    'email_id': email_id,
                    'category': analysis['category'],
                    'confidence': analysis['confidence'],
                    'mark_as_read': self._should_mark_as_read(analysis)
                }
                
                sorting_result = await self.sorter.process(sorter_input)
                
                # Record result
                result = {
                    'email_id': email_id,
                    'subject': subject,
                    'category': analysis['category'],
                    'confidence': analysis['confidence'],
                    'sentiment': analysis.get('sentiment', 'neutral'),
                    'priority': analysis.get('priority', 'low'),
                    'action_required': analysis.get('action_required', False),
                    'label_applied': sorting_result['label'],
                    'success': sorting_result['success'],
                    'summary': analysis.get('summary', '')
                }
                
                # Save detailed analysis if configured
                if self.save_analysis:
                    self._save_detailed_analysis(email_id, analysis)
                
                results.append(result)
                
                self.log(f"Completed processing email: {subject}")
            
            return {
                'processed': len(results),
                'results': results
            }
                
        except Exception as e:
            self.handle_error(e, "Error in coordinator workflow")
            return {
                'processed': 0,
                'results': [],
                'error': str(e)
            }
    
    def _handle_priority(self, email_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply special handling based on email priority."""
        priority = analysis.get('priority', 'low')
        action_required = analysis.get('action_required', False)
        
        result = {'priority_action': None}
        
        # Apply special handling for high priority emails
        if priority == 'high':
            # Apply special 'IMPORTANT' label for high priority
            try:
                self.gmail_client.apply_label(email_id, "IMPORTANT")
                result['priority_action'] = 'applied_important_label'
                self.log(f"Applied IMPORTANT label to high priority email: {email_id}")
            except Exception as e:
                self.log(f"Failed to apply IMPORTANT label: {str(e)}", level="error")
        
        # Apply action required label if needed
        if action_required:
            try:
                self.gmail_client.apply_label(email_id, "ACTION_REQUIRED")
                result['priority_action'] = 'applied_action_required_label'
                self.log(f"Applied ACTION_REQUIRED label to email: {email_id}")
            except Exception as e:
                self.log(f"Failed to apply ACTION_REQUIRED label: {str(e)}", level="error")
                
        return result
    
    def _should_mark_as_read(self, analysis: Dict[str, Any]) -> bool:
        """Determine if email should be marked as read based on analysis."""
        # Don't mark as read if high priority or requires action
        if analysis.get('priority', 'low') == 'high' or analysis.get('action_required', False):
            return False
        
        # Use default setting for other emails
        return self.auto_mark_as_read
    
    def _save_detailed_analysis(self, email_id: str, analysis: Dict[str, Any]) -> None:
        """Save detailed analysis results to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_results/{email_id}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
                
            self.log(f"Saved detailed analysis to {filename}")
        except Exception as e:
            self.log(f"Failed to save analysis results: {str(e)}", level="error")
    
    async def process_single_email(self, email_id: str) -> Dict[str, Any]:
        """Process a single email by ID."""
        try:
            # Fetch the specific email
            msg = self.gmail_client.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            # Extract email details
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
            
            email = {
                'id': email_id,
                'subject': subject,
                'sender': sender,
                'body': body
            }
            
            # Process the email
            analysis = await self.analyzer.process(email)
            
            # Apply priority-based processing
            priority_result = self._handle_priority(email_id, analysis)
            
            sorter_input = {
                'email_id': email_id,
                'category': analysis['category'],
                'confidence': analysis['confidence'],
                'mark_as_read': self._should_mark_as_read(analysis)
            }
            
            sorting_result = await self.sorter.process(sorter_input)
            
            # Save detailed analysis if configured
            if self.save_analysis:
                self._save_detailed_analysis(email_id, analysis)
            
            result = {
                'email_id': email_id,
                'subject': subject,
                'category': analysis['category'],
                'confidence': analysis['confidence'],
                'sentiment': analysis.get('sentiment', 'neutral'),
                'priority': analysis.get('priority', 'low'),
                'action_required': analysis.get('action_required', False),
                'action_items': analysis.get('action_items', []),
                'deadlines': analysis.get('deadlines', []),
                'label_applied': sorting_result['label'],
                'success': sorting_result['success'],
                'summary': analysis.get('summary', ''),
                'enhanced_data': analysis.get('enhanced_data', {})
            }
            
            return result
            
        except Exception as e:
            self.handle_error(e, f"Error processing email {email_id}")
            return {
                'email_id': email_id,
                'success': False,
                'error': str(e)
            } 