"""
Transaction Analyzer Agent

This agent provides comprehensive transaction analysis capabilities including
balance validation, amount verification, and transaction integrity checks.
It serves as a specialized component that can be used across different patterns.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from models.swift_message import SWIFTMessage
from models.transaction import ProcessedTransaction, TransactionSplit
from config import Config


class TransactionAnalyzer:
    """
    Dedicated transaction analysis and validation agent.
    
    This class handles:
    - Transaction balance validation
    - Amount precision handling
    - Split transaction verification
    - Financial integrity checks
    - Transaction pattern analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Financial precision settings
        self.decimal_places = 2
        self.rounding = ROUND_HALF_UP
        
        self.logger.info("Transaction Analyzer initialized")
    
    def validate_transaction_balance(self, transaction: ProcessedTransaction) -> Dict[str, Any]:
        """
        Validate that transaction splits balance correctly
        
        Returns:
            Dict with validation results including errors and corrections
        """
        try:
            original_amount = self._normalize_amount(transaction.amount)
            total_splits = Decimal('0')
            
            validation_result = {
                "is_balanced": False,
                "original_amount": float(original_amount),
                "total_splits": 0.0,
                "difference": 0.0,
                "splits_count": len(transaction.splits),
                "errors": [],
                "suggested_correction": None
            }
            
            # Calculate total of all splits
            all_splits = []
            if hasattr(transaction, 'company_split') and transaction.company_split:
                all_splits.append(transaction.company_split)
            if hasattr(transaction, 'credit_splits') and transaction.credit_splits:
                all_splits.extend(transaction.credit_splits)
            if hasattr(transaction, 'debit_splits') and transaction.debit_splits:
                all_splits.extend(transaction.debit_splits)
            
            for split in all_splits:
                split_amount = self._normalize_amount(split.amount)
                total_splits += split_amount
            
            validation_result["total_splits"] = float(total_splits)
            difference = original_amount - total_splits
            validation_result["difference"] = float(difference)
            
            # Check if balanced (within tolerance)
            tolerance = Decimal('0.01')  # 1 cent tolerance
            if abs(difference) <= tolerance:
                validation_result["is_balanced"] = True
            else:
                validation_result["errors"].append(
                    f"Transaction splits do not balance: {float(difference)} difference"
                )
                
                # Suggest correction
                validation_result["suggested_correction"] = self._suggest_balance_correction(
                    transaction, difference
                )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Balance validation failed for transaction {transaction.transaction_id}: {str(e)}")
            return {
                "is_balanced": False,
                "errors": [f"Validation error: {str(e)}"],
                "original_amount": 0.0,
                "total_splits": 0.0,
                "difference": 0.0,
                "splits_count": 0
            }
    
    def fix_transaction_balance(self, transaction: ProcessedTransaction) -> ProcessedTransaction:
        """
        Automatically fix transaction balance issues
        
        Returns:
            Fixed transaction with balanced splits
        """
        try:
            validation = self.validate_transaction_balance(transaction)
            
            if validation["is_balanced"]:
                return transaction  # Already balanced
            
            original_amount = self._normalize_amount(transaction.amount)
            difference = Decimal(str(validation["difference"]))
            
            # Adjust existing splits
            transaction = self._adjust_splits_for_balance(transaction, difference)
            
            self.logger.info(f"Fixed balance for transaction {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            self.logger.error(f"Failed to fix balance for transaction {transaction.transaction_id}: {str(e)}")
            return transaction
    
    def analyze_transaction_patterns(self, transactions: List[ProcessedTransaction]) -> Dict[str, Any]:
        """
        Analyze patterns across multiple transactions
        
        Returns:
            Analysis results including statistics and anomalies
        """
        if not transactions:
            return {"error": "No transactions to analyze"}
        
        analysis = {
            "total_transactions": len(transactions),
            "total_amount": 0.0,
            "average_amount": 0.0,
            "amount_distribution": {},
            "balance_issues": 0,
            "split_patterns": {},
            "currency_breakdown": {},
            "anomalies": []
        }
        
        try:
            amounts = []
            currencies = {}
            balance_issues = 0
            split_counts = {}
            
            for transaction in transactions:
                # Amount analysis
                amount = float(self._normalize_amount(transaction.amount))
                amounts.append(amount)
                
                # Currency tracking
                currency = getattr(transaction, 'currency', 'USD')
                currencies[currency] = currencies.get(currency, 0) + 1
                
                # Balance validation
                validation = self.validate_transaction_balance(transaction)
                if not validation["is_balanced"]:
                    balance_issues += 1
                
                # Split pattern analysis
                split_count = len(transaction.splits)
                split_counts[split_count] = split_counts.get(split_count, 0) + 1
            
            # Calculate statistics
            if amounts:
                analysis["total_amount"] = sum(amounts)
                analysis["average_amount"] = sum(amounts) / len(amounts)
                analysis["amount_distribution"] = {
                    "min": min(amounts),
                    "max": max(amounts),
                    "median": sorted(amounts)[len(amounts)//2]
                }
            
            analysis["balance_issues"] = balance_issues
            analysis["currency_breakdown"] = currencies
            analysis["split_patterns"] = split_counts
            
            # Detect anomalies
            if amounts:
                avg_amount = analysis["average_amount"]
                for amount in amounts:
                    if amount > avg_amount * 10:  # 10x average
                        analysis["anomalies"].append(f"High amount transaction: ${amount:,.2f}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {str(e)}")
            analysis["error"] = str(e)
            return analysis
    
    def convert_swift_to_transaction(self, swift_message: SWIFTMessage) -> ProcessedTransaction:
        """
        Convert SWIFT message to Transaction with proper splits
        
        Returns:
            Transaction object with balanced splits
        """
        try:
            # Create simple balanced splits
            amount_decimal = self._normalize_amount(swift_message.amount)
            
            # Company fee split (5%)
            company_split = TransactionSplit(
                original_message_id=swift_message.message_id,
                split_type="COMPANY",
                amount=amount_decimal * Decimal('0.05'),
                currency=swift_message.currency,
                description="Company processing fee"
            )
            
            # Credit split (95%)
            credit_split = TransactionSplit(
                original_message_id=swift_message.message_id,
                split_type="CREDIT",
                amount=amount_decimal * Decimal('0.95'),
                currency=swift_message.currency,
                description="Transaction credit"
            )
            
            # Create transaction
            transaction = ProcessedTransaction(
                original_message_id=swift_message.message_id,
                original_amount=amount_decimal,
                currency=swift_message.currency,
                company_split=company_split,
                account_splits=[],
                credit_splits=[credit_split],
                debit_splits=[],
                processing_time=0.001
            )
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Failed to convert SWIFT message {swift_message.message_id}: {str(e)}")
            raise
    
    def batch_validate_transactions(self, transactions: List[ProcessedTransaction]) -> Dict[str, Any]:
        """
        Validate multiple transactions in batch
        
        Returns:
            Batch validation results
        """
        results = {
            "total_transactions": len(transactions),
            "balanced_transactions": 0,
            "unbalanced_transactions": 0,
            "total_difference": 0.0,
            "validation_details": []
        }
        
        for transaction in transactions:
            validation = self.validate_transaction_balance(transaction)
            results["validation_details"].append({
                "transaction_id": transaction.transaction_id,
                "is_balanced": validation["is_balanced"],
                "difference": validation["difference"]
            })
            
            if validation["is_balanced"]:
                results["balanced_transactions"] += 1
            else:
                results["unbalanced_transactions"] += 1
                results["total_difference"] += abs(validation["difference"])
        
        return results
    
    def _normalize_amount(self, amount: Any) -> Decimal:
        """Normalize amount to Decimal with proper precision"""
        if isinstance(amount, str):
            # Remove any non-numeric characters except decimal point
            cleaned = ''.join(c for c in amount if c.isdigit() or c == '.')
            return Decimal(cleaned).quantize(Decimal('0.01'), rounding=self.rounding)
        elif isinstance(amount, (int, float)):
            return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=self.rounding)
        elif isinstance(amount, Decimal):
            return amount.quantize(Decimal('0.01'), rounding=self.rounding)
        else:
            raise ValueError(f"Invalid amount type: {type(amount)}")
    
    def _create_default_splits(self, amount: Decimal, message_id: str, currency: str) -> Tuple[TransactionSplit, List[TransactionSplit]]:
        """Create default balanced splits for a transaction"""
        
        # Default split: 5% company fee, 95% to credit
        company_amount = amount * Decimal('0.05')
        credit_amount = amount * Decimal('0.95')
        
        company_split = TransactionSplit(
            original_message_id=message_id,
            split_type="COMPANY",
            amount=company_amount,
            currency=currency,
            description="Company processing fee"
        )
        
        credit_split = TransactionSplit(
            original_message_id=message_id,
            split_type="CREDIT", 
            amount=credit_amount,
            currency=currency,
            description="Transaction credit"
        )
        
        return company_split, [credit_split]
    
    def _adjust_splits_for_balance(self, transaction: ProcessedTransaction, difference: Decimal) -> ProcessedTransaction:
        """Adjust existing splits to achieve balance"""
        if difference == 0:
            return transaction
        
        # Adjust the company split to absorb the difference
        if transaction.company_split:
            current_amount = self._normalize_amount(transaction.company_split.amount)
            new_amount = current_amount + difference
            
            # Create new company split with adjusted amount
            adjusted_company_split = TransactionSplit(
                original_message_id=transaction.company_split.original_message_id,
                split_type=transaction.company_split.split_type,
                amount=new_amount,
                currency=transaction.company_split.currency,
                description=transaction.company_split.description
            )
            
            # Return updated transaction
            return ProcessedTransaction(
                original_message_id=transaction.original_message_id,
                original_amount=transaction.original_amount,
                currency=transaction.currency,
                company_split=adjusted_company_split,
                account_splits=transaction.account_splits,
                credit_splits=transaction.credit_splits,
                debit_splits=transaction.debit_splits,
                processing_time=transaction.processing_time
            )
        
        return transaction
    
    def _suggest_balance_correction(self, transaction: ProcessedTransaction, difference: Decimal) -> Dict[str, Any]:
        """Suggest how to correct balance issues"""
        return {
            "method": "adjust_first_split",
            "adjustment_amount": float(difference),
            "description": f"Add {float(difference)} to first split to balance transaction"
        }