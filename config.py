"""
Configuration settings for the SWIFT processing system
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for the SWIFT processing system"""
    
    # System settings
    MESSAGE_COUNT = 10
    BANK_COUNT = 5
    
    # Processing settings
    MAX_WORKERS = 8
    BATCH_SIZE = 50
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
    OPENAI_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
    
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as a dictionary"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
