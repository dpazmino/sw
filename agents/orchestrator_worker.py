"""
Orchestrator-Worker Agent Pattern for transaction splitting and processing
"""

import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, ROUND_HALF_UP
import time

from models.swift_message import SWIFTMessage
from models.transaction import TransactionSplit, ProcessedTransaction
from services.database import DatabaseService
from config import Config


class OrchestratorWorker:
    """
    Orchestrator-Worker pattern implementation for SWIFT transaction processing
    Orchestrator coordinates multiple workers to split transactions into components
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.db_service = DatabaseService()
        self.max_workers = 4  # Number of worker threads
    
    def process_transactions(self, messages: List[SWIFTMessage]) -> List[ProcessedTransaction]:
        """
        Main orchestrator method - coordinates workers to process transactions
        """
        self.logger.info(f"Orchestrator starting processing of {len(messages)} transactions")
        
        start_time = time.time()
        processed_transactions = []
        
        # Orchestrator distributes work to workers
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit work to workers
            future_to_message = {
                executor.submit(self._worker_process_transaction, message): message
                for message in messages
            }
            
            # Orchestrator collects results from workers
            completed_count = 0
            for future in as_completed(future_to_message):
                original_message = future_to_message[future]
                
                try:
                    processed_transaction = future.result()
                    processed_transactions.append(processed_transaction)
                    completed_count += 1
                    
                    if completed_count % 50 == 0:
                        self.logger.info(f"Orchestrator processed {completed_count}/{len(messages)} transactions")
                        
                except Exception as e:
                    self.logger.error(f"Worker failed to process transaction {original_message.message_id}: {str(e)}")
        
        processing_time = time.time() - start_time
        
        # Orchestrator validates all work is complete
        self._orchestrator_validate_results(processed_transactions, messages)
        
        # Orchestrator persists results
        self._orchestrator_persist_results(processed_transactions)
        
        self.logger.info(f"Orchestrator completed processing in {processing_time:.2f} seconds")
        
        return processed_transactions
    
    def _worker_process_transaction(self, message: SWIFTMessage) -> ProcessedTransaction:
        """
        Worker method - processes a single transaction
        """
        worker_start_time = time.time()
        
        self.logger.debug(f"Worker processing transaction {message.message_id}")
        
        original_amount = Decimal(message.amount)
        
        # Worker creates transaction splits
        company_split = self._worker_create_company_split(message, original_amount)
        account_splits = self._worker_create_account_splits(message, original_amount)
        credit_splits = self._worker_create_credit_splits(message, original_amount)
        debit_splits = self._worker_create_debit_splits(message, original_amount)
        
        # Worker assembles final transaction
        processing_time = time.time() - worker_start_time
        
        processed_transaction = ProcessedTransaction(
            original_message_id=message.message_id,
            original_amount=original_amount,
            currency=message.currency,
            company_split=company_split,
            account_splits=account_splits,
            credit_splits=credit_splits,
            debit_splits=debit_splits,
            processing_time=processing_time
        )
        
        # Worker validates its work
        if not processed_transaction.validate_splits():
            self.logger.error(f"Worker validation failed for transaction {message.message_id}")
            raise ValueError("Transaction splits do not balance")
        
        self.logger.debug(f"Worker completed transaction {message.message_id} in {processing_time:.4f} seconds")
        
        return processed_transaction
    
    def _worker_create_company_split(self, message: SWIFTMessage, original_amount: Decimal) -> TransactionSplit:
        """
        Worker creates company fee split
        """
        company_fee_rate = Decimal(str(self.config.COMPANY_PERCENTAGE))
        company_amount = (original_amount * company_fee_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return TransactionSplit(
            original_message_id=message.message_id,
            split_type="COMPANY",
            amount=company_amount,
            currency=message.currency,
            description=f"Company processing fee ({self.config.COMPANY_PERCENTAGE * 100}%)"
        )
    
    def _worker_create_account_splits(self, message: SWIFTMessage, original_amount: Decimal) -> List[TransactionSplit]:
        """
        Worker creates account-related splits - simplified to avoid double counting
        """
        # No separate account splits to avoid double counting
        # All accounting is handled through credit/debit splits
        return []
    
    def _worker_create_credit_splits(self, message: SWIFTMessage, original_amount: Decimal) -> List[TransactionSplit]:
        """
        Worker creates credit-related splits
        """
        splits = []
        
        # Credit to receiver (main transaction amount minus fees)
        company_fee_rate = Decimal(str(self.config.COMPANY_PERCENTAGE))
        credit_amount = (original_amount * (Decimal('1') - company_fee_rate)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        splits.append(TransactionSplit(
            original_message_id=message.message_id,
            split_type="CREDIT",
            amount=credit_amount,
            currency=message.currency,
            account_number=self._generate_account_number(message.receiver_bic),
            description=f"Credit to receiver - {message.receiver_bic}"
        ))
        
        return splits
    
    def _worker_create_debit_splits(self, message: SWIFTMessage, original_amount: Decimal) -> List[TransactionSplit]:
        """
        Worker creates debit-related splits
        """
        splits = []
        
        # Debit from sender (full original amount)
        splits.append(TransactionSplit(
            original_message_id=message.message_id,
            split_type="DEBIT",
            amount=original_amount,
            currency=message.currency,
            account_number=self._generate_account_number(message.sender_bic),
            description=f"Debit from sender - {message.sender_bic}"
        ))
        
        return splits
    
    def _generate_account_number(self, bic: str) -> str:
        """
        Generate account number from BIC (simplified)
        """
        # In a real system, this would look up actual account numbers
        # For demo purposes, generate based on BIC
        import hashlib
        hash_object = hashlib.md5(bic.encode())
        hex_dig = hash_object.hexdigest()
        return f"ACC{hex_dig[:8].upper()}"
    
    def _orchestrator_validate_results(self, processed_transactions: List[ProcessedTransaction], 
                                     original_messages: List[SWIFTMessage]) -> None:
        """
        Orchestrator validates all worker results
        """
        self.logger.info("Orchestrator validating worker results...")
        
        validation_errors = []
        
        # Check count matches
        if len(processed_transactions) != len(original_messages):
            validation_errors.append(f"Transaction count mismatch: expected {len(original_messages)}, got {len(processed_transactions)}")
        
        # Validate each transaction
        for transaction in processed_transactions:
            if not transaction.validate_splits():
                validation_errors.append(f"Transaction {transaction.original_message_id} splits do not balance")
        
        # Calculate totals
        original_total = sum(Decimal(msg.amount) for msg in original_messages)
        processed_total = sum(transaction.original_amount for transaction in processed_transactions)
        
        if abs(original_total - processed_total) > Decimal('0.01'):
            validation_errors.append(f"Total amount mismatch: original {original_total}, processed {processed_total}")
        
        if validation_errors:
            self.logger.error(f"Orchestrator validation failed: {validation_errors}")
            raise ValueError(f"Validation errors: {validation_errors}")
        
        self.logger.info("Orchestrator validation passed")
    
    def _orchestrator_persist_results(self, processed_transactions: List[ProcessedTransaction]) -> None:
        """
        Orchestrator persists all results to database
        """
        self.logger.info(f"Orchestrator persisting {len(processed_transactions)} transactions...")
        
        try:
            # Convert to database format
            transaction_records = []
            for transaction in processed_transactions:
                record = {
                    'transaction_id': transaction.transaction_id,
                    'original_message_id': transaction.original_message_id,
                    'original_amount': float(transaction.original_amount),
                    'currency': transaction.currency,
                    'company_fee': float(transaction.company_split.amount),
                    'split_count': len(transaction.account_splits) + len(transaction.credit_splits) + len(transaction.debit_splits) + 1,
                    'processing_time': transaction.processing_time,
                    'processed_at': transaction.created_at.isoformat()
                }
                transaction_records.append(record)
            
            # Persist to database
            self.db_service.save_processed_transactions(transaction_records)
            
            self.logger.info("Orchestrator successfully persisted all transactions")
            
        except Exception as e:
            self.logger.error(f"Orchestrator failed to persist results: {str(e)}")
            raise
    
    def get_processing_summary(self, processed_transactions: List[ProcessedTransaction]) -> Dict[str, Any]:
        """
        Generate processing summary statistics
        """
        if not processed_transactions:
            return {}
        
        total_amount = sum(transaction.original_amount for transaction in processed_transactions)
        total_company_fees = sum(transaction.company_split.amount for transaction in processed_transactions)
        avg_processing_time = sum(transaction.processing_time for transaction in processed_transactions) / len(processed_transactions)
        
        total_splits = sum(
            len(transaction.account_splits) + len(transaction.credit_splits) + 
            len(transaction.debit_splits) + 1  # +1 for company split
            for transaction in processed_transactions
        )
        
        summary = {
            "total_transactions": len(processed_transactions),
            "total_amount_processed": float(total_amount),
            "total_company_fees": float(total_company_fees),
            "average_processing_time": avg_processing_time,
            "total_splits_created": total_splits,
            "average_splits_per_transaction": total_splits / len(processed_transactions),
            "fee_percentage": float(total_company_fees / total_amount * 100) if total_amount > 0 else 0
        }
        
        return summary
