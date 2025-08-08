"""
Database service for CSV-based transaction storage and management
"""

import csv
import logging
import os
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from models.swift_message import SWIFTMessage
from models.bank import Bank
from config import Config


class DatabaseService:
    """
    CSV-based database service for SWIFT transaction processing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Ensure data directory exists
        os.makedirs(self.config.DATABASE_PATH, exist_ok=True)
        
        self.logger.info("Database Service initialized")
    
    def initialize_database(self) -> None:
        """
        Initialize database files and structure
        """
        self.logger.info("Initializing database structure...")
        
        # Initialize banks CSV
        self._initialize_banks_csv()
        
        # Initialize transactions CSV
        self._initialize_transactions_csv()
        
        # Initialize processed transactions CSV
        self._initialize_processed_transactions_csv()
        
        # Initialize fraud reviews CSV
        self._initialize_fraud_reviews_csv()
        
        self.logger.info("Database initialization completed")
    
    def _initialize_banks_csv(self) -> None:
        """
        Initialize banks CSV file
        """
        banks_file = self.config.BANKS_FILE
        
        if not os.path.exists(banks_file):
            headers = [
                'bic_code', 'bank_name', 'country_code', 'city', 
                'address', 'risk_score', 'transaction_volume'
            ]
            
            with open(banks_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            
            self.logger.debug(f"Created banks CSV: {banks_file}")
    
    def _initialize_transactions_csv(self) -> None:
        """
        Initialize transactions CSV file
        """
        transactions_file = self.config.TRANSACTIONS_FILE
        
        if not os.path.exists(transactions_file):
            headers = [
                'message_id', 'message_type', 'reference', 'amount', 'currency',
                'sender_bic', 'receiver_bic', 'value_date', 'ordering_customer',
                'beneficiary', 'remittance_info', 'validation_status', 'validation_errors',
                'fraud_status', 'fraud_score', 'processing_status', 'created_at', 'processed_at'
            ]
            
            with open(transactions_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            
            self.logger.debug(f"Created transactions CSV: {transactions_file}")
    
    def _initialize_processed_transactions_csv(self) -> None:
        """
        Initialize processed transactions CSV file
        """
        processed_file = os.path.join(self.config.DATABASE_PATH, "processed_transactions.csv")
        
        if not os.path.exists(processed_file):
            headers = [
                'transaction_id', 'original_message_id', 'original_amount', 'currency',
                'company_fee', 'split_count', 'processing_time', 'processed_at'
            ]
            
            with open(processed_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            
            self.logger.debug(f"Created processed transactions CSV: {processed_file}")
    
    def _initialize_fraud_reviews_csv(self) -> None:
        """
        Initialize fraud reviews CSV file
        """
        fraud_file = os.path.join(self.config.DATABASE_PATH, "fraud_reviews.csv")
        
        if not os.path.exists(fraud_file):
            headers = [
                'review_id', 'message_id', 'decision', 'confidence', 'reasoning',
                'risk_factors', 'recommended_actions', 'reviewed_at', 'reviewer'
            ]
            
            with open(fraud_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            
            self.logger.debug(f"Created fraud reviews CSV: {fraud_file}")
    
    def save_banks(self, banks: List[Bank]) -> None:
        """
        Save banks to CSV database
        """
        self.logger.info(f"Saving {len(banks)} banks to database")
        
        banks_file = self.config.BANKS_FILE
        
        # Convert banks to dictionaries
        bank_data = []
        for bank in banks:
            bank_data.append({
                'bic_code': bank.bic_code,
                'bank_name': bank.bank_name,
                'country_code': bank.country_code,
                'city': bank.city,
                'address': bank.address,
                'risk_score': bank.risk_score,
                'transaction_volume': bank.transaction_volume
            })
        
        # Write to CSV
        with open(banks_file, 'w', newline='', encoding='utf-8') as csvfile:
            if bank_data:
                fieldnames = bank_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(bank_data)
        
        self.logger.debug(f"Saved {len(banks)} banks to {banks_file}")
    
    def update_transactions(self, messages: List[SWIFTMessage]) -> None:
        """
        Update transactions CSV with processed messages
        """
        self.logger.info(f"Updating database with {len(messages)} transactions")
        
        transactions_file = self.config.TRANSACTIONS_FILE
        
        # Convert messages to dictionaries
        transaction_data = []
        for message in messages:
            transaction_data.append({
                'message_id': message.message_id,
                'message_type': message.message_type,
                'reference': message.reference,
                'amount': message.amount,
                'currency': message.currency,
                'sender_bic': message.sender_bic,
                'receiver_bic': message.receiver_bic,
                'value_date': message.value_date,
                'ordering_customer': getattr(message, 'ordering_customer', ''),
                'beneficiary': getattr(message, 'beneficiary', ''),
                'remittance_info': getattr(message, 'remittance_info', ''),
                'validation_status': message.validation_status,
                'validation_errors': '|'.join(message.validation_errors),
                'fraud_status': message.fraud_status,
                'fraud_score': message.fraud_score or 0.0,
                'processing_status': message.processing_status,
                'created_at': message.created_at.isoformat(),
                'processed_at': message.processed_at.isoformat() if message.processed_at else ''
            })
        
        # Write to CSV (append mode)
        file_exists = os.path.exists(transactions_file)
        
        with open(transactions_file, 'a', newline='', encoding='utf-8') as csvfile:
            if transaction_data:
                fieldnames = transaction_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header only if file is new
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(transaction_data)
        
        self.logger.debug(f"Updated transactions database with {len(messages)} records")
    
    def save_processed_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        """
        Save processed transaction records
        """
        self.logger.info(f"Saving {len(transactions)} processed transactions")
        
        processed_file = os.path.join(self.config.DATABASE_PATH, "processed_transactions.csv")
        
        # Append to CSV
        file_exists = os.path.exists(processed_file)
        
        with open(processed_file, 'a', newline='', encoding='utf-8') as csvfile:
            if transactions:
                fieldnames = transactions[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header only if file is new
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(transactions)
        
        self.logger.debug(f"Saved {len(transactions)} processed transactions")
    
    def save_fraud_review(self, review_data: Dict[str, Any]) -> None:
        """
        Save fraud review record
        """
        fraud_file = os.path.join(self.config.DATABASE_PATH, "fraud_reviews.csv")
        
        # Append to CSV
        file_exists = os.path.exists(fraud_file)
        
        with open(fraud_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'review_id', 'message_id', 'decision', 'confidence', 'reasoning',
                'risk_factors', 'recommended_actions', 'reviewed_at', 'reviewer'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            # Convert lists to strings for CSV storage
            review_record = review_data.copy()
            if 'risk_factors' in review_record and isinstance(review_record['risk_factors'], list):
                review_record['risk_factors'] = '|'.join(review_record['risk_factors'])
            if 'recommended_actions' in review_record and isinstance(review_record['recommended_actions'], list):
                review_record['recommended_actions'] = '|'.join(review_record['recommended_actions'])
            
            writer.writerow(review_record)
        
        self.logger.debug(f"Saved fraud review for message {review_data.get('message_id')}")
    
    def get_transaction_statistics(self) -> Dict[str, Any]:
        """
        Get transaction statistics from database
        """
        try:
            transactions_file = self.config.TRANSACTIONS_FILE
            
            if not os.path.exists(transactions_file):
                return {}
            
            # Read transactions using pandas
            df = pd.read_csv(transactions_file)
            
            if df.empty:
                return {}
            
            stats = {
                'total_transactions': len(df),
                'total_amount': df['amount'].astype(float).sum(),
                'average_amount': df['amount'].astype(float).mean(),
                'fraud_count': len(df[df['fraud_status'] == 'FRAUDULENT']),
                'held_count': len(df[df['fraud_status'] == 'HELD']),
                'clean_count': len(df[df['fraud_status'] == 'CLEAN']),
                'currency_distribution': df['currency'].value_counts().to_dict(),
                'message_type_distribution': df['message_type'].value_counts().to_dict(),
                'validation_status_distribution': df['validation_status'].value_counts().to_dict()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating transaction statistics: {str(e)}")
            return {}
    
    def get_fraud_summary(self) -> Dict[str, Any]:
        """
        Get fraud detection summary
        """
        try:
            transactions_file = self.config.TRANSACTIONS_FILE
            fraud_file = os.path.join(self.config.DATABASE_PATH, "fraud_reviews.csv")
            
            summary = {}
            
            # Transaction fraud stats
            if os.path.exists(transactions_file):
                df = pd.read_csv(transactions_file)
                if not df.empty:
                    summary['fraud_detection'] = {
                        'total_analyzed': len(df),
                        'fraudulent': len(df[df['fraud_status'] == 'FRAUDULENT']),
                        'held_for_review': len(df[df['fraud_status'] == 'HELD']),
                        'clean': len(df[df['fraud_status'] == 'CLEAN']),
                        'average_fraud_score': df['fraud_score'].astype(float).mean()
                    }
            
            # LLM review stats
            if os.path.exists(fraud_file):
                df_reviews = pd.read_csv(fraud_file)
                if not df_reviews.empty:
                    summary['llm_reviews'] = {
                        'total_reviews': len(df_reviews),
                        'decisions': df_reviews['decision'].value_counts().to_dict(),
                        'average_confidence': df_reviews['confidence'].astype(float).mean()
                    }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error calculating fraud summary: {str(e)}")
            return {}
    
    def export_results(self, output_dir: str = None) -> str:
        """
        Export all results to a summary report
        """
        if output_dir is None:
            output_dir = self.config.DATABASE_PATH
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"processing_report_{timestamp}.txt")
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("SWIFT Transaction Processing Report\n")
                f.write("=" * 50 + "\n\n")
                
                # Transaction statistics
                trans_stats = self.get_transaction_statistics()
                if trans_stats:
                    f.write("TRANSACTION STATISTICS\n")
                    f.write("-" * 30 + "\n")
                    for key, value in trans_stats.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")
                
                # Fraud summary
                fraud_summary = self.get_fraud_summary()
                if fraud_summary:
                    f.write("FRAUD DETECTION SUMMARY\n")
                    f.write("-" * 30 + "\n")
                    for section, data in fraud_summary.items():
                        f.write(f"{section.upper()}:\n")
                        for key, value in data.items():
                            f.write(f"  {key}: {value}\n")
                        f.write("\n")
                
                f.write(f"Report generated at: {datetime.now().isoformat()}\n")
            
            self.logger.info(f"Report exported to: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            return ""
