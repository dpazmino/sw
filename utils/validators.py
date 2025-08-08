"""
SWIFT message validation utilities
"""

import re
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from models.swift_message import SWIFTMessage
from config import Config


class ValidationResult(BaseModel):
    """Result of validation operation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)


class SWIFTValidator:
    """
    Comprehensive SWIFT message validator
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # BIC validation patterns
        self.bic_pattern = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')
        
        # Valid ISO currency codes (major ones)
        self.valid_currencies = {
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'SGD', 'HKD',
            'KRW', 'CNY', 'INR', 'BRL', 'MXN', 'ZAR', 'RUB', 'TRY',
            'THB', 'MYR', 'IDR', 'PHP', 'VND', 'EGP', 'SAR', 'AED',
            'QAR', 'KWD', 'BHD', 'OMR', 'JOD', 'LBP', 'ILS', 'CLP',
            'COP', 'PEN', 'UYU', 'ARS', 'BOB', 'PYG', 'CRC', 'GTQ',
            'HNL', 'NIO', 'PAB', 'DOP', 'JMD', 'TTD', 'BBD', 'XCD'
        }
        
        # High-risk country codes (examples for demonstration)
        self.high_risk_countries = {
            'AF', 'BY', 'CF', 'CG', 'CU', 'CD', 'ER', 'GN', 'GW',
            'HT', 'IR', 'IQ', 'LB', 'LR', 'LY', 'ML', 'MM', 'NI',
            'KP', 'RU', 'SO', 'SS', 'SD', 'SY', 'VE', 'YE', 'ZW'
        }
        
        self.logger.info("SWIFT Validator initialized")
    
    def validate_swift_message(self, message: SWIFTMessage) -> ValidationResult:
        """
        Comprehensive SWIFT message validation
        """
        result = ValidationResult(is_valid=True)
        
        # Basic field validation
        self._validate_basic_fields(message, result)
        
        # BIC validation
        self._validate_bic_codes(message, result)
        
        # Amount validation
        self._validate_amount(message, result)
        
        # Currency validation
        self._validate_currency(message, result)
        
        # Date validation
        self._validate_dates(message, result)
        
        # Message type specific validation
        self._validate_message_type_specific(message, result)
        
        # Business rules validation
        self._validate_business_rules(message, result)
        
        # Format validation
        self._validate_formats(message, result)
        
        # Risk validation
        self._validate_risk_factors(message, result)
        
        self.logger.debug(f"Validation completed for message {message.message_id}: "
                         f"{'VALID' if result.is_valid else 'INVALID'} "
                         f"({len(result.errors)} errors, {len(result.warnings)} warnings)")
        
        return result
    
    def _validate_basic_fields(self, message: SWIFTMessage, result: ValidationResult):
        """Validate basic required fields"""
        required_fields = self.config.SWIFT_STANDARDS["required_fields"]
        
        for field in required_fields:
            value = getattr(message, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                result.add_error(f"Required field '{field}' is missing or empty")
    
    def _validate_bic_codes(self, message: SWIFTMessage, result: ValidationResult):
        """Validate BIC code formats"""
        # Sender BIC validation
        if not self._is_valid_bic(message.sender_bic):
            result.add_error(f"Invalid sender BIC format: {message.sender_bic}")
        
        # Receiver BIC validation
        if not self._is_valid_bic(message.receiver_bic):
            result.add_error(f"Invalid receiver BIC format: {message.receiver_bic}")
        
        # Same BIC check
        if message.sender_bic == message.receiver_bic:
            result.add_error("Sender and receiver BIC codes cannot be identical")
        
        # High-risk country check
        sender_country = message.sender_bic[4:6] if len(message.sender_bic) >= 6 else ""
        receiver_country = message.receiver_bic[4:6] if len(message.receiver_bic) >= 6 else ""
        
        if sender_country in self.high_risk_countries:
            result.add_warning(f"Sender BIC from high-risk country: {sender_country}")
        
        if receiver_country in self.high_risk_countries:
            result.add_warning(f"Receiver BIC from high-risk country: {receiver_country}")
    
    def _validate_amount(self, message: SWIFTMessage, result: ValidationResult):
        """Validate transaction amount"""
        try:
            amount = float(message.amount)
            
            # Range validation
            if amount <= 0:
                result.add_error("Amount must be positive")
            
            if amount < self.config.SWIFT_STANDARDS["min_amount"]:
                result.add_error(f"Amount {amount} below minimum {self.config.SWIFT_STANDARDS['min_amount']}")
            
            if amount > self.config.SWIFT_STANDARDS["max_amount"]:
                result.add_error(f"Amount {amount} exceeds maximum {self.config.SWIFT_STANDARDS['max_amount']}")
            
            # Format validation
            if '.' in message.amount:
                decimal_places = len(message.amount.split('.')[1])
                if decimal_places > 2:
                    result.add_error("Amount cannot have more than 2 decimal places")
            
            # Suspicious amount patterns
            if amount >= 10000 and amount % 1000 == 0:
                result.add_warning(f"Round amount may indicate structuring: {amount}")
            
            # Very large amounts
            if amount >= 1000000:
                result.add_warning(f"Very large transaction amount: {amount}")
            
        except (ValueError, TypeError):
            result.add_error(f"Invalid amount format: {message.amount}")
    
    def _validate_currency(self, message: SWIFTMessage, result: ValidationResult):
        """Validate currency code"""
        if not message.currency:
            result.add_error("Currency code is required")
            return
        
        if len(message.currency) != 3:
            result.add_error(f"Currency code must be 3 characters: {message.currency}")
        
        if not message.currency.isalpha():
            result.add_error(f"Currency code must be alphabetic: {message.currency}")
        
        if not message.currency.isupper():
            result.add_error(f"Currency code must be uppercase: {message.currency}")
        
        if message.currency not in self.valid_currencies:
            result.add_warning(f"Uncommon or invalid currency code: {message.currency}")
    
    def _validate_dates(self, message: SWIFTMessage, result: ValidationResult):
        """Validate date fields"""
        # Value date validation (YYMMDD format)
        if not self._is_valid_value_date(message.value_date):
            result.add_error(f"Invalid value date format (YYMMDD required): {message.value_date}")
        else:
            # Check if date is reasonable
            try:
                year = 2000 + int(message.value_date[:2])
                month = int(message.value_date[2:4])
                day = int(message.value_date[4:6])
                
                value_date = datetime(year, month, day)
                now = datetime.now()
                
                # Value date should be within reasonable range
                days_diff = (value_date - now).days
                
                if days_diff < -30:
                    result.add_warning(f"Value date is more than 30 days in the past: {message.value_date}")
                
                if days_diff > 30:
                    result.add_warning(f"Value date is more than 30 days in the future: {message.value_date}")
                
                # Weekend/holiday warning (simplified)
                if value_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    result.add_warning("Value date falls on weekend")
                
            except (ValueError, IndexError):
                result.add_error(f"Invalid value date: {message.value_date}")
    
    def _validate_message_type_specific(self, message: SWIFTMessage, result: ValidationResult):
        """Validate message type specific requirements"""
        if message.message_type not in self.config.SWIFT_STANDARDS["valid_message_types"]:
            result.add_error(f"Invalid message type: {message.message_type}")
            return
        
        if message.message_type == "MT103":
            # MT103 specific validations
            if not getattr(message, 'ordering_customer', None):
                result.add_warning("MT103 should include ordering customer information")
            
            if not getattr(message, 'beneficiary', None):
                result.add_warning("MT103 should include beneficiary information")
            
            if not getattr(message, 'remittance_info', None):
                result.add_warning("MT103 should include remittance information")
        
        elif message.message_type == "MT202":
            # MT202 specific validations
            # MT202 is for bank-to-bank transfers, simpler requirements
            pass
    
    def _validate_business_rules(self, message: SWIFTMessage, result: ValidationResult):
        """Validate business logic rules"""
        # Reference validation
        if len(message.reference) > self.config.SWIFT_STANDARDS["max_reference_length"]:
            result.add_error(f"Reference exceeds maximum length of {self.config.SWIFT_STANDARDS['max_reference_length']}")
        
        # Reference should not be empty or only whitespace
        if not message.reference.strip():
            result.add_error("Reference cannot be empty")
        
        # Reference should not contain invalid characters
        if not re.match(r'^[A-Za-z0-9/\-\?\:\(\)\.\,\'\+\s]+$', message.reference):
            result.add_error("Reference contains invalid characters")
        
        # Check for suspicious reference patterns
        if re.match(r'^(TEST|FAKE|DEMO)', message.reference.upper()):
            result.add_warning("Reference appears to be test data")
    
    def _validate_formats(self, message: SWIFTMessage, result: ValidationResult):
        """Validate field formats"""
        # Check for proper SWIFT character set
        swift_charset = re.compile(r'^[A-Za-z0-9/\-\?\:\(\)\.\,\'\+\s]*$')
        
        if message.reference and not swift_charset.match(message.reference):
            result.add_error("Reference contains invalid SWIFT characters")
        
        if hasattr(message, 'ordering_customer') and message.ordering_customer:
            if not swift_charset.match(message.ordering_customer):
                result.add_error("Ordering customer contains invalid SWIFT characters")
        
        if hasattr(message, 'beneficiary') and message.beneficiary:
            if not swift_charset.match(message.beneficiary):
                result.add_error("Beneficiary contains invalid SWIFT characters")
        
        if hasattr(message, 'remittance_info') and message.remittance_info:
            if not swift_charset.match(message.remittance_info):
                result.add_error("Remittance info contains invalid SWIFT characters")
    
    def _validate_risk_factors(self, message: SWIFTMessage, result: ValidationResult):
        """Validate risk-related factors"""
        # Check for patterns indicating potential fraud
        risk_patterns = [
            r'.*999.*',
            r'.*000000.*',
            r'TEST.*',
            r'FAKE.*',
            r'DEMO.*'
        ]
        
        for pattern in risk_patterns:
            if re.match(pattern, message.reference, re.IGNORECASE):
                result.add_warning(f"Reference matches risk pattern: {pattern}")
            
            if re.match(pattern, message.sender_bic, re.IGNORECASE):
                result.add_warning(f"Sender BIC matches risk pattern: {pattern}")
            
            if re.match(pattern, message.receiver_bic, re.IGNORECASE):
                result.add_warning(f"Receiver BIC matches risk pattern: {pattern}")
    
    def _is_valid_bic(self, bic: str) -> bool:
        """Check if BIC format is valid"""
        if not bic:
            return False
        
        return bool(self.bic_pattern.match(bic))
    
    def _is_valid_value_date(self, value_date: str) -> bool:
        """Check if value date format is valid (YYMMDD)"""
        if not value_date or len(value_date) != 6:
            return False
        
        if not value_date.isdigit():
            return False
        
        try:
            year = int(value_date[:2])
            month = int(value_date[2:4])
            day = int(value_date[4:6])
            
            # Basic range checks
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            
            # Try to create date to validate
            datetime(2000 + year, month, day)
            return True
            
        except (ValueError, IndexError):
            return False
    
    def validate_batch(self, messages: List[SWIFTMessage]) -> Tuple[List[ValidationResult], dict]:
        """
        Validate a batch of messages and return summary statistics
        """
        self.logger.info(f"Validating batch of {len(messages)} messages")
        
        results = []
        valid_count = 0
        total_errors = 0
        total_warnings = 0
        
        for message in messages:
            result = self.validate_swift_message(message)
            results.append(result)
            
            if result.is_valid:
                valid_count += 1
            
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
        
        summary = {
            'total_messages': len(messages),
            'valid_messages': valid_count,
            'invalid_messages': len(messages) - valid_count,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'validation_rate': (valid_count / len(messages)) * 100 if messages else 0
        }
        
        self.logger.info(f"Batch validation completed: {valid_count}/{len(messages)} valid "
                        f"({summary['validation_rate']:.1f}%)")
        
        return results, summary
    
    def get_common_errors(self, results: List[ValidationResult]) -> dict:
        """
        Analyze validation results to find common error patterns
        """
        error_counts = {}
        warning_counts = {}
        
        for result in results:
            for error in result.errors:
                # Normalize error message for counting
                normalized_error = re.sub(r'[:\'"]\s*[^:]*$', '', error)
                error_counts[normalized_error] = error_counts.get(normalized_error, 0) + 1
            
            for warning in result.warnings:
                # Normalize warning message for counting
                normalized_warning = re.sub(r'[:\'"]\s*[^:]*$', '', warning)
                warning_counts[normalized_warning] = warning_counts.get(normalized_warning, 0) + 1
        
        return {
            'common_errors': dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)),
            'common_warnings': dict(sorted(warning_counts.items(), key=lambda x: x[1], reverse=True))
        }


class SWIFTMessageCorrector:
    """
    SWIFT message correction utilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = SWIFTValidator()
    
    def auto_correct_message(self, message: SWIFTMessage) -> Tuple[SWIFTMessage, List[str]]:
        """
        Attempt automatic correction of common SWIFT message errors
        """
        corrected_message = message.copy(deep=True)
        corrections_made = []
        
        # Fix common BIC issues
        corrected_message, bic_corrections = self._fix_bic_issues(corrected_message)
        corrections_made.extend(bic_corrections)
        
        # Fix amount formatting
        corrected_message, amount_corrections = self._fix_amount_formatting(corrected_message)
        corrections_made.extend(amount_corrections)
        
        # Fix currency code
        corrected_message, currency_corrections = self._fix_currency_code(corrected_message)
        corrections_made.extend(currency_corrections)
        
        # Fix reference formatting
        corrected_message, ref_corrections = self._fix_reference_formatting(corrected_message)
        corrections_made.extend(ref_corrections)
        
        # Fix value date
        corrected_message, date_corrections = self._fix_value_date(corrected_message)
        corrections_made.extend(date_corrections)
        
        if corrections_made:
            self.logger.info(f"Auto-corrected message {message.message_id}: {corrections_made}")
        
        return corrected_message, corrections_made
    
    def _fix_bic_issues(self, message: SWIFTMessage) -> Tuple[SWIFTMessage, List[str]]:
        """Fix common BIC formatting issues"""
        corrections = []
        
        # Fix case
        if message.sender_bic != message.sender_bic.upper():
            message.sender_bic = message.sender_bic.upper()
            corrections.append("Converted sender BIC to uppercase")
        
        if message.receiver_bic != message.receiver_bic.upper():
            message.receiver_bic = message.receiver_bic.upper()
            corrections.append("Converted receiver BIC to uppercase")
        
        # Remove spaces
        sender_cleaned = message.sender_bic.replace(' ', '')
        if sender_cleaned != message.sender_bic:
            message.sender_bic = sender_cleaned
            corrections.append("Removed spaces from sender BIC")
        
        receiver_cleaned = message.receiver_bic.replace(' ', '')
        if receiver_cleaned != message.receiver_bic:
            message.receiver_bic = receiver_cleaned
            corrections.append("Removed spaces from receiver BIC")
        
        return message, corrections
    
    def _fix_amount_formatting(self, message: SWIFTMessage) -> Tuple[SWIFTMessage, List[str]]:
        """Fix amount formatting issues"""
        corrections = []
        
        try:
            # Parse and reformat amount
            amount_float = float(message.amount)
            formatted_amount = f"{amount_float:.2f}"
            
            if formatted_amount != message.amount:
                message.amount = formatted_amount
                corrections.append("Standardized amount formatting to 2 decimal places")
        
        except ValueError:
            # Try to clean common issues
            cleaned_amount = message.amount.replace(',', '').replace(' ', '')
            try:
                amount_float = float(cleaned_amount)
                message.amount = f"{amount_float:.2f}"
                corrections.append("Cleaned and formatted amount")
            except ValueError:
                pass
        
        return message, corrections
    
    def _fix_currency_code(self, message: SWIFTMessage) -> Tuple[SWIFTMessage, List[str]]:
        """Fix currency code formatting"""
        corrections = []
        
        if message.currency != message.currency.upper():
            message.currency = message.currency.upper()
            corrections.append("Converted currency code to uppercase")
        
        # Remove spaces
        cleaned_currency = message.currency.replace(' ', '')
        if cleaned_currency != message.currency:
            message.currency = cleaned_currency
            corrections.append("Removed spaces from currency code")
        
        return message, corrections
    
    def _fix_reference_formatting(self, message: SWIFTMessage) -> Tuple[SWIFTMessage, List[str]]:
        """Fix reference formatting issues"""
        corrections = []
        
        # Trim whitespace
        trimmed_ref = message.reference.strip()
        if trimmed_ref != message.reference:
            message.reference = trimmed_ref
            corrections.append("Trimmed whitespace from reference")
        
        # Convert to uppercase for consistency
        upper_ref = message.reference.upper()
        if upper_ref != message.reference:
            message.reference = upper_ref
            corrections.append("Converted reference to uppercase")
        
        # Truncate if too long
        max_length = self.validator.config.SWIFT_STANDARDS["max_reference_length"]
        if len(message.reference) > max_length:
            message.reference = message.reference[:max_length]
            corrections.append(f"Truncated reference to {max_length} characters")
        
        return message, corrections
    
    def _fix_value_date(self, message: SWIFTMessage) -> Tuple[SWIFTMessage, List[str]]:
        """Fix value date formatting"""
        corrections = []
        
        # Remove spaces and non-digits
        cleaned_date = ''.join(c for c in message.value_date if c.isdigit())
        
        if len(cleaned_date) == 8:  # YYYYMMDD format
            # Convert to YYMMDD
            yy = cleaned_date[2:4]
            mm = cleaned_date[4:6]
            dd = cleaned_date[6:8]
            new_date = f"{yy}{mm}{dd}"
            
            if new_date != message.value_date:
                message.value_date = new_date
                corrections.append("Converted value date from YYYYMMDD to YYMMDD format")
        
        elif len(cleaned_date) == 6 and cleaned_date != message.value_date:
            message.value_date = cleaned_date
            corrections.append("Cleaned value date format")
        
        return message, corrections
