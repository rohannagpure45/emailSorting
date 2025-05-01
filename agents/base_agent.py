from abc import ABC, abstractmethod
from typing import Any, Dict
import google.generativeai as genai
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        
        # Load API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        
        # Configure Gemini
        if api_key:
            genai.configure(api_key=api_key)
            # Initialize the generative model
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            self.llm = genai  # Keep a reference to the module if needed
        else:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
        logger.add(f"logs/{name}.log", rotation="1 day")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results."""
        pass

    def log(self, message: str, level: str = "info"):
        """Log messages with different severity levels."""
        log_func = getattr(logger, level.lower())
        log_func(f"[{self.name}] {message}")

    def handle_error(self, error: Exception, context: str = ""):
        """Handle and log errors consistently."""
        error_msg = f"Error in {self.name}: {str(error)}"
        if context:
            error_msg += f" Context: {context}"
        logger.error(error_msg)
        raise error 