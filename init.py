#!/usr/bin/env python3
import os
import json
import sys
from loguru import logger
from dotenv import load_dotenv

logger.remove()
logger.add(sys.stdout, level="INFO")

def setup_directories():
    """Create necessary directories."""
    dirs = ["logs", "config", "analysis_results"]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def create_env_file():
    """Create .env file if not exists."""
    if not os.path.exists(".env"):
        with open(".env", "w") as env_file:
            env_file.write("""# Google API credentials - REQUIRED, must be valid or the application will not start
GOOGLE_API_KEY=your_gemini_api_key_here

# Gmail API paths
GMAIL_CREDENTIALS_PATH=config/credentials.json
GMAIL_TOKEN_PATH=config/token.json""")
        logger.info("Created .env file")

def check_credentials():
    """Check if Gmail API credentials exist."""
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "config/credentials.json")
    
    if not os.path.exists(creds_path):
        logger.warning(f"Gmail API credentials not found at {creds_path}")
        logger.info("Please follow these steps to set up Gmail API:")
        logger.info("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        logger.info("2. Create a new project or select an existing one")
        logger.info("3. Enable the Gmail API")
        logger.info("4. Create OAuth 2.0 credentials")
        logger.info("5. Download the credentials JSON file")
        logger.info(f"6. Save it as {creds_path}")
    else:
        logger.info(f"Gmail API credentials found at {creds_path}")

def create_default_config():
    """Create default configuration file."""
    config_path = "config/config.json"
    if not os.path.exists(config_path):
        default_config = {
            "batch_size": 10,
            "confidence_threshold": 0.5,
            "auto_mark_as_read": True,
            "save_analysis": True,
            "model_name": "gemini-2.0-flash",
            "priority_labels": True,
            "sentiment_analysis": True,
            "extract_action_items": True,
            "extract_deadlines": True,
            "label_mappings": {
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
            },
            "priority_label_mappings": {
                "high": "IMPORTANT",
                "action_required": "ACTION_REQUIRED"
            }
        }
        
        with open(config_path, "w") as config_file:
            json.dump(default_config, config_file, indent=2)
        logger.info(f"Created default configuration at {config_path}")

def main():
    """Run initialization steps."""
    logger.info("Initializing Email Sorting Agent...")
    load_dotenv()
    
    setup_directories()
    create_env_file()
    check_credentials()
    create_default_config()
    
    logger.info("Initialization complete!")
    logger.info("To run the application, use: python main.py")
    logger.info("For enhanced analysis, try: python main.py --detailed-output")

if __name__ == "__main__":
    main() 