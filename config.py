"""
Configuration settings for the SWIFT processing system
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for the SWIFT processing system"""
    
    # System settings
    MESSAGE_COUNT = 1000
    BANK_COUNT = 30
    
    # Processing settings
    MAX_WORKERS = 8
    BATCH_SIZE = 50
    
    # Database settings
    DATABASE_PATH = "data"
    BANKS_FILE = "data/banks.csv"
    TRANSACTIONS_FILE = "data/transactions.csv"
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    OPENAI_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
    
    # SWIFT validation settings
    SWIFT_STANDARDS = {
        "max_reference_length": 16,
        "max_amount": 999999999.99,
        "min_amount": 0.01,
        "required_fields": ["message_type", "reference", "amount", "sender_bic", "receiver_bic"],
        "valid_message_types": ["MT103", "MT202"]
    }
    
    # Fraud detection settings
    BENFORD_THRESHOLD = 0.05  # Chi-square test threshold
    FRAUD_REVIEW_THRESHOLD = 0.7  # LLM confidence threshold
    
    # Transaction splitting settings
    COMPANY_PERCENTAGE = 0.1  # 10% company fee
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as a dictionary"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
