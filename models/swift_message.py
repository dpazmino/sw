"""
SWIFT message models and validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import uuid


class SWIFTMessage(BaseModel):
    """SWIFT message model with validation"""
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: Literal["MT103", "MT202"]
    reference: str = Field(max_length=16)
    amount: str = Field(pattern=r'^\d+\.\d{2}$')
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')
    sender_bic: str = Field(pattern=r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')
    receiver_bic: str = Field(pattern=r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')
    value_date: str = Field(pattern=r'^\d{6}$')  # YYMMDD format
    
    # Additional MT103 fields
    ordering_customer: Optional[str] = None
    beneficiary: Optional[str] = None
    remittance_info: Optional[str] = None
    
    # Processing status fields
    validation_status: str = Field(default="PENDING")
    validation_errors: list = Field(default_factory=list)
    fraud_status: str = Field(default="PENDING")
    fraud_score: Optional[float] = None
    processing_status: str = Field(default="PENDING")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount format and range"""
        try:
            amount_float = float(v)
            if amount_float <= 0:
                raise ValueError("Amount must be positive")
            if amount_float > 999999999.99:
                raise ValueError("Amount exceeds maximum limit")
            return f"{amount_float:.2f}"
        except ValueError as e:
            raise ValueError(f"Invalid amount format: {e}")
    
    @validator('reference')
    def validate_reference(cls, v):
        """Validate reference format"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Reference cannot be empty")
        return v.strip().upper()
    
    def to_swift_format(self) -> str:
        """Convert to SWIFT message format"""
        if self.message_type == "MT103":
            return self._format_mt103()
        elif self.message_type == "MT202":
            return self._format_mt202()
        else:
            raise ValueError(f"Unsupported message type: {self.message_type}")
    
    def _format_mt103(self) -> str:
        """Format as MT103 message"""
        lines = [
            f":20:{self.reference}",
            f":32A:{self.value_date}{self.currency}{self.amount}",
            f":50K:{self.ordering_customer or 'ORDERING CUSTOMER'}",
            f":59:{self.beneficiary or 'BENEFICIARY'}",
            f":70:{self.remittance_info or 'PAYMENT PURPOSE'}"
        ]
        return "\n".join(lines)
    
    def _format_mt202(self) -> str:
        """Format as MT202 message"""
        lines = [
            f":20:{self.reference}",
            f":32A:{self.value_date}{self.currency}{self.amount}",
            f":58A:{self.receiver_bic}"
        ]
        return "\n".join(lines)
    
    def get_first_digit(self) -> int:
        """Get first digit of amount for Benford's law analysis"""
        amount_str = self.amount.replace('.', '').lstrip('0')
        return int(amount_str[0]) if amount_str else 0
    
    def mark_as_fraudulent(self, score: float, reason: str):
        """Mark message as fraudulent"""
        self.fraud_status = "FRAUDULENT"
        self.fraud_score = score
        self.validation_errors.append(f"FRAUD: {reason}")
    
    def mark_as_held(self, score: float, reason: str):
        """Mark message as held for review"""
        self.fraud_status = "HELD"
        self.fraud_score = score
        self.validation_errors.append(f"HOLD: {reason}")
    
    def mark_as_clean(self, score: float = 0.0):
        """Mark message as clean"""
        self.fraud_status = "CLEAN"
        self.fraud_score = score
    
    class Config:
        arbitrary_types_allowed = True
