#!/usr/bin/env python3
import os
import sys
from loguru import logger
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from dotenv import load_dotenv

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

def test_gemini_api():
    """Test Gemini API connection."""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in .env file")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Test that we can generate content
        response = model.generate_content("Hello, world!")
        logger.info("Gemini API connection successful!")
        return True
    except Exception as e:
        logger.error(f"Gemini API test failed: {str(e)}")
        return False

def test_gmail_api():
    """Test Gmail API connection."""
    try:
        creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "config/credentials.json")
        token_path = os.getenv("GMAIL_TOKEN_PATH", "config/token.json")
        
        if not os.path.exists(creds_path):
            logger.error(f"Gmail API credentials not found at {creds_path}")
            return False
        
        # Get credentials
        creds = None
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, ['https://www.googleapis.com/auth/gmail.modify'])
                creds = flow.run_local_server(port=0)
                
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Test service connection
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        logger.info(f"Gmail API connection successful! Email: {profile.get('emailAddress')}")
        return True
    except Exception as e:
        logger.error(f"Gmail API test failed: {str(e)}")
        return False

def main():
    """Run setup tests."""
    load_dotenv()
    logger.info("Testing Email Sorting Agent setup...")
    
    # Check directories
    for directory in ["logs", "config"]:
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    # Test APIs
    gemini_ok = test_gemini_api()
    gmail_ok = test_gmail_api()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Gemini API: {'OK' if gemini_ok else 'FAILED'}")
    logger.info(f"Gmail API: {'OK' if gmail_ok else 'FAILED'}")
    
    if gemini_ok and gmail_ok:
        logger.info("\nAll tests passed! You're ready to run the application.")
        logger.info("Run: python main.py")
        return 0
    else:
        logger.error("\nSome tests failed. Please fix the issues before running the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 