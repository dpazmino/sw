"""
Transaction models for processing and splitting
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid


class TransactionSplit(BaseModel):
    """Individual transaction split"""
    
    split_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_message_id: str
    split_type: str  # "COMPANY", "ACCOUNT", "CREDIT", "DEBIT"
    amount: Decimal
    currency: str = "USD"
    account_number: Optional[str] = None
    description: str
    created_at: datetime = Field(default_factory=datetime.now)


class ProcessedTransaction(BaseModel):
    """Fully processed transaction with all splits"""
    
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_message_id: str
    original_amount: Decimal
    currency: str = "USD"
    
    # Transaction splits
    company_split: TransactionSplit
    account_splits: List[TransactionSplit] = Field(default_factory=list)
    credit_splits: List[TransactionSplit] = Field(default_factory=list)
    debit_splits: List[TransactionSplit] = Field(default_factory=list)
    
    # Processing metadata
    processed_by: str = "orchestrator_worker"
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def total_splits_amount(self) -> Decimal:
        """Calculate total amount across all splits"""
        total = self.company_split.amount
        
        for split_list in [self.account_splits, self.credit_splits, self.debit_splits]:
            total += sum(split.amount for split in split_list)
        
        return total
    
    def validate_splits(self) -> bool:
        """Validate that splits add up to original amount"""
        return abs(self.total_splits_amount - self.original_amount) < Decimal('0.01')


class FraudReviewResult(BaseModel):
    """Result from LLM fraud review"""
    
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str
    decision: str  # "APPROVE", "REJECT", "INVESTIGATE"
    confidence: float
    reasoning: str
    risk_factors: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    reviewed_at: datetime = Field(default_factory=datetime.now)
    reviewer: str = "llm_fraud_analyst"
