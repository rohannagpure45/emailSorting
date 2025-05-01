import os
import json
from typing import Dict, Any
from loguru import logger
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class EmailSorterConfig(BaseModel):
    # Gmail API settings
    gmail_credentials_path: str = Field(
        default_factory=lambda: os.getenv("GMAIL_CREDENTIALS_PATH", "config/credentials.json")
    )
    gmail_token_path: str = Field(
        default_factory=lambda: os.getenv("GMAIL_TOKEN_PATH", "config/token.json")
    )
    
    # LLM settings
    google_api_key: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", "")
    )
    model_name: str = Field(default="gemini-2.0-flash")
    
    # Coordinator settings
    batch_size: int = Field(default=10)
    confidence_threshold: float = Field(default=0.5)
    auto_mark_as_read: bool = Field(default=True)
    save_analysis: bool = Field(default=True)
    
    # Analysis settings
    priority_labels: bool = Field(default=True)  # Whether to apply priority-based labels
    sentiment_analysis: bool = Field(default=True)  # Whether to perform sentiment analysis
    extract_action_items: bool = Field(default=True)  # Whether to extract action items
    extract_deadlines: bool = Field(default=True)  # Whether to extract deadlines
    
    # Category to label mappings
    label_mappings: Dict[str, str] = Field(
        default={
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
    )
    
    # Priority labels
    priority_label_mappings: Dict[str, str] = Field(
        default={
            "high": "IMPORTANT",
            "action_required": "ACTION_REQUIRED"
        }
    )

class ConfigHandler:
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> EmailSorterConfig:
        """Load configuration from file or create default."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    config_data = json.load(file)
                    return EmailSorterConfig(**config_data)
            else:
                # Create default config
                config = EmailSorterConfig()
                self._save_config(config)
                return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return EmailSorterConfig()
    
    def _save_config(self, config: EmailSorterConfig) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as file:
                json.dump(config.model_dump(), file, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def get_config(self) -> EmailSorterConfig:
        """Get the current configuration."""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> EmailSorterConfig:
        """Update configuration with new values."""
        try:
            # Get current config as dict
            config_dict = self.config.model_dump()
            
            # Update the values
            for key, value in updates.items():
                if key in config_dict:
                    config_dict[key] = value
            
            # Create new config object
            self.config = EmailSorterConfig(**config_dict)
            
            # Save to file
            self._save_config(self.config)
            
            return self.config
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return self.config 