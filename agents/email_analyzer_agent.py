from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from loguru import logger
import re
from datetime import datetime
import time
from dashboard.database import log_email_processing, update_daily_stats

class EmailAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__("EmailAnalyzerAgent")
        self.categories = {
            # Primary categories
            "work": "Professional or work-related emails, business communications",
            "personal": "Personal messages from friends and family",
            "promotional": "Marketing and promotional content from businesses",
            "finance": "Banking, investments, bills, payments, and financial statements",
            "travel": "Flight confirmations, hotel bookings, itineraries, travel updates",
            "shopping": "Order confirmations, shipping updates, receipts from online stores",
            "social": "Social media notifications and updates",
            "news": "News alerts, newsletters, and subscriptions",
            "health": "Medical appointments, health insurance, fitness trackers",
            "education": "Courses, learning materials, academic communications",
            "events": "Invitations, event announcements, RSVPs, calendar items",
            "updates": "Software updates, account notifications, service announcements",
            "forums": "Discussion groups, community messages, forum notifications",
            "legal": "Legal documents, contracts, terms of service updates",
            "other": "Uncategorized emails"
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email content and determine its category along with enhanced analysis.
        
        Args:
            input_data: Dictionary containing email data
                - subject: Email subject
                - body: Email body content
                - sender: Email sender address
        
        Returns:
            Dictionary containing:
                - category: Determined category
                - confidence: Confidence score (0-1)
                - reasoning: Explanation for the categorization
                - enhanced_data: Category-specific structured data
                - sentiment: Sentiment analysis (positive, negative, neutral)
                - priority: Priority level (high, medium, low)
                - action_required: Whether the email requires action
                - action_items: List of action items if any
                - deadlines: List of deadlines or important dates if any
                - summary: Brief summary of the email content
        """
        start_time = time.time()
        success = False
        result = {
            "category": "other",
            "confidence": 0.0,
            "reasoning": "Error during analysis",
            "enhanced_data": {},
            "sentiment": "neutral",
            "priority": "low",
            "action_required": False,
            "action_items": [],
            "deadlines": [],
            "summary": "Error occurred during analysis"
        }
        
        try:
            self.log(f"Analyzing email: {input_data.get('subject', 'No subject')}")
            
            # Step 1: Basic categorization
            category_prompt = self._create_category_prompt(input_data)
            category_response = await self.model.generate_content_async(category_prompt)
            
            # Parse the basic categorization
            result = self._parse_category_response(category_response.text)
            category = result["category"]
            
            self.log(f"Basic categorization complete. Category: {category}")
            
            # Step 2: Enhanced analysis based on category
            enhanced_data = await self._perform_enhanced_analysis(input_data, category)
            
            # Merge results
            result.update(enhanced_data)
            
            self.log(f"Enhanced analysis complete for category: {category}")
            success = True
            return result
            
        except Exception as e:
            self.handle_error(e, "Failed to analyze email")
            return result
        finally:
            # Log performance data
            processing_time = time.time() - start_time
            log_email_processing(
                email_id=input_data.get('id', 'unknown'),
                subject=input_data.get('subject', 'No subject'),
                category=result['category'],
                confidence=result['confidence'],
                processing_time=processing_time,
                success=success
            )
            
            # Update daily stats
            update_daily_stats()

    def _create_category_prompt(self, email_data: Dict[str, Any]) -> str:
        """Create a prompt for the LLM to categorize the email."""
        categories_str = "\n".join([f"- {k}: {v}" for k, v in self.categories.items()])
        
        return f"""
        Analyze the following email and categorize it into exactly ONE of these categories:
        {categories_str}

        Email Details:
        Subject: {email_data.get('subject', 'No subject')}
        Sender: {email_data.get('sender', 'Unknown sender')}
        Body: {email_data.get('body', 'No body')}

        Please provide:
        1. The single most appropriate category from the list (use ONLY category names listed above)
        2. A confidence score between 0 and 1
        3. A brief explanation of why this category was chosen

        Format your response as:
        Category: [category]
        Confidence: [score]
        Reasoning: [explanation]
        """

    def _parse_category_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for basic categorization."""
        lines = response.strip().split('\n')
        result = {
            "category": "other",
            "confidence": 0.0,
            "reasoning": ""
        }
        
        for line in lines:
            if line.startswith("Category:"):
                result["category"] = line.split(":")[1].strip().lower()
            elif line.startswith("Confidence:"):
                try:
                    result["confidence"] = float(line.split(":")[1].strip())
                except ValueError:
                    result["confidence"] = 0.0
            elif line.startswith("Reasoning:"):
                result["reasoning"] = line.split(":")[1].strip()
        
        # Validate category
        if result["category"] not in self.categories:
            result["category"] = "other"
            
        return result

    async def _perform_enhanced_analysis(self, email_data: Dict[str, Any], category: str) -> Dict[str, Any]:
        """
        Perform enhanced analysis based on email category.
        This extracts structured data, sentiment, priorities, and more.
        """
        prompt = self._create_enhanced_analysis_prompt(email_data, category)
        response = await self.model.generate_content_async(prompt)
        
        return self._parse_enhanced_analysis(response.text, category)
    
    def _create_enhanced_analysis_prompt(self, email_data: Dict[str, Any], category: str) -> str:
        """Create a prompt for enhanced analysis based on email category."""
        # Base prompt for all categories
        base_prompt = f"""
        Perform detailed analysis of the following email that has been categorized as '{category}':
        
        Subject: {email_data.get('subject', 'No subject')}
        Sender: {email_data.get('sender', 'Unknown sender')}
        Body: {email_data.get('body', 'No body')}
        
        Please provide:
        1. Sentiment (positive, negative, or neutral)
        2. Priority level (high, medium, or low)
        3. Whether this email requires any action (true or false)
        4. Action items (list any tasks or actions needed)
        5. Important dates or deadlines mentioned (in YYYY-MM-DD format)
        6. A brief summary (max 50 words)
        """
        
        # Add category-specific analysis requests
        if category == "work":
            base_prompt += """
            7. Project name (if mentioned)
            8. Colleagues or team members mentioned
            9. Meeting details (time, location, participants)
            10. Deadline criticality (urgent, standard, flexible)
            """
        elif category == "events":
            base_prompt += """
            7. Event name
            8. Event date and time
            9. Event location
            10. Organizer
            11. Required response (RSVP needed?)
            """
        elif category == "finance":
            base_prompt += """
            7. Transaction type (payment, bill, statement, etc.)
            8. Amount mentioned (with currency)
            9. Due date (if applicable)
            10. Account information (last 4 digits if shown)
            """
        elif category == "travel":
            base_prompt += """
            7. Travel type (flight, hotel, car, etc.)
            8. Booking reference/confirmation number
            9. Departure/arrival information
            10. Dates of travel
            11. Location details
            """
        elif category == "shopping":
            base_prompt += """
            7. Order number/reference
            8. Store/vendor name
            9. Product(s) purchased
            10. Shipping information
            11. Total amount (with currency)
            """
        
        base_prompt += """
        Format your response as JSON:
        {
          "sentiment": "positive/negative/neutral",
          "priority": "high/medium/low",
          "action_required": true/false,
          "action_items": ["item1", "item2"],
          "deadlines": ["YYYY-MM-DD"],
          "summary": "Brief summary here",
          "category_data": {
            // category-specific fields
          }
        }
        """
        
        return base_prompt
    
    def _parse_enhanced_analysis(self, response: str, category: str) -> Dict[str, Any]:
        """Parse the enhanced analysis response."""
        try:
            # Extract JSON from response
            json_pattern = r"\{[\s\S]*\}"
            match = re.search(json_pattern, response)
            
            if not match:
                raise ValueError("No valid JSON found in response")
                
            json_str = match.group(0)
            
            # Try to manually extract fields if JSON parsing fails
            result = {
                "sentiment": self._extract_field(response, "sentiment", "neutral"),
                "priority": self._extract_field(response, "priority", "low"),
                "action_required": self._extract_boolean(response, "action_required", False),
                "action_items": self._extract_list(response, "action_items"),
                "deadlines": self._extract_list(response, "deadlines"),
                "summary": self._extract_field(response, "summary", "No summary available"),
                "enhanced_data": {}
            }
            
            # Extract category-specific data
            category_data = {}
            if category == "work":
                category_data = {
                    "project": self._extract_field(response, "project", ""),
                    "colleagues": self._extract_list(response, "colleagues"),
                    "meeting_details": self._extract_field(response, "meeting_details", ""),
                    "deadline_criticality": self._extract_field(response, "deadline_criticality", "standard")
                }
            elif category == "events":
                category_data = {
                    "event_name": self._extract_field(response, "event_name", ""),
                    "event_date": self._extract_field(response, "event_date", ""),
                    "event_location": self._extract_field(response, "event_location", ""),
                    "organizer": self._extract_field(response, "organizer", ""),
                    "rsvp_needed": self._extract_boolean(response, "rsvp_needed", False)
                }
            elif category == "finance":
                category_data = {
                    "transaction_type": self._extract_field(response, "transaction_type", ""),
                    "amount": self._extract_field(response, "amount", ""),
                    "due_date": self._extract_field(response, "due_date", ""),
                    "account_info": self._extract_field(response, "account_info", "")
                }
            elif category == "travel":
                category_data = {
                    "travel_type": self._extract_field(response, "travel_type", ""),
                    "booking_reference": self._extract_field(response, "booking_reference", ""),
                    "departure_arrival": self._extract_field(response, "departure_arrival", ""),
                    "travel_dates": self._extract_field(response, "travel_dates", ""),
                    "location": self._extract_field(response, "location", "")
                }
            elif category == "shopping":
                category_data = {
                    "order_number": self._extract_field(response, "order_number", ""),
                    "store": self._extract_field(response, "store", ""),
                    "products": self._extract_list(response, "products"),
                    "shipping_info": self._extract_field(response, "shipping_info", ""),
                    "total_amount": self._extract_field(response, "total_amount", "")
                }
            
            result["enhanced_data"] = category_data
            return result
            
        except Exception as e:
            self.log(f"Error parsing enhanced analysis: {str(e)}", level="error")
            return {
                "sentiment": "neutral",
                "priority": "low",
                "action_required": False,
                "action_items": [],
                "deadlines": [],
                "summary": "Failed to extract enhanced analysis",
                "enhanced_data": {}
            }
    
    def _extract_field(self, text: str, field_name: str, default: str) -> str:
        """Extract a field value from response text."""
        pattern = rf'"{field_name}"\s*:\s*"([^"]*)"'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        
        # Try without quotes for value
        pattern = rf'"{field_name}"\s*:\s*([^,\}}]+)'
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if value not in ["true", "false", "null"]:
                return value
        
        return default
    
    def _extract_boolean(self, text: str, field_name: str, default: bool) -> bool:
        """Extract a boolean value from response text."""
        pattern = rf'"{field_name}"\s*:\s*(true|false)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).lower() == "true"
        return default
    
    def _extract_list(self, text: str, field_name: str) -> List[str]:
        """Extract a list value from response text."""
        pattern = rf'"{field_name}"\s*:\s*\[(.*?)\]'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            items_str = match.group(1)
            # Parse items in the list
            items = []
            for item in re.finditer(r'"([^"]*)"', items_str):
                items.append(item.group(1))
            return items
        return [] 