"""
Fraud detection service using various techniques
"""

import logging
from typing import Tuple, List, Dict, Any
import numpy as np
from datetime import datetime
import re

from models.swift_message import SWIFTMessage


class FraudDetectionService:
    """
    Comprehensive fraud detection service
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Fraud detection thresholds
        self.high_amount_threshold = 1000000  # $1M
        self.round_amount_threshold = 10000   # Detect round amounts above $10K
        self.velocity_threshold = 5           # Max transactions per timeframe
        
        # Risk patterns
        self.high_risk_patterns = [
            r'TEST.*',
            r'FAKE.*',
            r'DEMO.*',
            r'.*999.*',
            r'.*000000.*'
        ]
        
        self.logger.info("Fraud Detection Service initialized")
    
    def analyze_transaction(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Perform comprehensive fraud analysis on a transaction
        """
        fraud_indicators = []
        risk_scores = []
        
        # Amount-based analysis
        amount_score, amount_indicators = self._analyze_amount_risk(message)
        risk_scores.append(amount_score)
        fraud_indicators.extend(amount_indicators)
        
        # Pattern-based analysis
        pattern_score, pattern_indicators = self._analyze_pattern_risk(message)
        risk_scores.append(pattern_score)
        fraud_indicators.extend(pattern_indicators)
        
        # Structural analysis
        structure_score, structure_indicators = self._analyze_structure_risk(message)
        risk_scores.append(structure_score)
        fraud_indicators.extend(structure_indicators)
        
        # Reference analysis
        ref_score, ref_indicators = self._analyze_reference_risk(message)
        risk_scores.append(ref_score)
        fraud_indicators.extend(ref_indicators)
        
        # Calculate overall fraud score
        overall_score = np.mean(risk_scores) if risk_scores else 0.0
        
        self.logger.debug(f"Transaction {message.message_id} fraud analysis: score={overall_score:.3f}, indicators={len(fraud_indicators)}")
        
        return overall_score, fraud_indicators
    
    def _analyze_amount_risk(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze amount-related fraud risks
        """
        indicators = []
        risk_score = 0.0
        
        try:
            amount = float(message.amount)
            
            # Very high amounts
            if amount > self.high_amount_threshold:
                indicators.append(f"Very high amount: ${amount:,.2f}")
                risk_score += 0.3
            
            # Round amounts (potential structuring)
            if amount >= self.round_amount_threshold and amount % 1000 == 0:
                indicators.append(f"Round amount suggesting structuring: ${amount:,.2f}")
                risk_score += 0.2
            
            # Unusual precision for large amounts
            if amount > 100000:
                decimal_part = message.amount.split('.')[1] if '.' in message.amount else "00"
                if decimal_part not in ["00", "50"]:  # Unusual cents for large amounts
                    indicators.append("Unusual precision for large amount")
                    risk_score += 0.1
            
            # Suspiciously low amounts for international transfers
            if amount < 10:
                indicators.append("Suspiciously low amount for international transfer")
                risk_score += 0.2
            
            # Check for common fraud amount patterns
            amount_str = str(int(amount))
            if self._has_repeated_digits(amount_str):
                indicators.append("Amount contains repeated digit patterns")
                risk_score += 0.15
            
        except ValueError:
            indicators.append("Invalid amount format")
            risk_score = 0.8
        
        return min(1.0, risk_score), indicators
    
    def _analyze_pattern_risk(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze pattern-based fraud risks
        """
        indicators = []
        risk_score = 0.0
        
        # Check BIC patterns
        for pattern in self.high_risk_patterns:
            if re.match(pattern, message.sender_bic, re.IGNORECASE):
                indicators.append(f"Sender BIC matches high-risk pattern: {pattern}")
                risk_score += 0.4
            
            if re.match(pattern, message.receiver_bic, re.IGNORECASE):
                indicators.append(f"Receiver BIC matches high-risk pattern: {pattern}")
                risk_score += 0.4
        
        # Check for identical sender/receiver
        if message.sender_bic == message.receiver_bic:
            indicators.append("Sender and receiver are identical")
            risk_score += 0.5
        
        # Check reference patterns
        if re.match(r'^(TEST|FAKE|DEMO)', message.reference, re.IGNORECASE):
            indicators.append("Reference contains test patterns")
            risk_score += 0.3
        
        # Check for sequential patterns in reference
        if self._has_sequential_pattern(message.reference):
            indicators.append("Reference contains sequential patterns")
            risk_score += 0.2
        
        return min(1.0, risk_score), indicators
    
    def _analyze_structure_risk(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze structural fraud risks
        """
        indicators = []
        risk_score = 0.0
        
        # Validate BIC structure
        if not self._is_valid_bic_structure(message.sender_bic):
            indicators.append("Invalid sender BIC structure")
            risk_score += 0.3
        
        if not self._is_valid_bic_structure(message.receiver_bic):
            indicators.append("Invalid receiver BIC structure")
            risk_score += 0.3
        
        # Check value date
        if not self._is_valid_value_date(message.value_date):
            indicators.append("Invalid or suspicious value date")
            risk_score += 0.2
        
        # Check currency code
        if not self._is_valid_currency(message.currency):
            indicators.append("Invalid currency code")
            risk_score += 0.2
        
        # Check message type consistency
        if message.message_type == "MT103" and not message.ordering_customer:
            indicators.append("MT103 missing ordering customer information")
            risk_score += 0.1
        
        return min(1.0, risk_score), indicators
    
    def _analyze_reference_risk(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze reference-related fraud risks
        """
        indicators = []
        risk_score = 0.0
        
        ref = message.reference
        
        # Check for overly simple references
        if len(set(ref)) <= 2:  # Very few unique characters
            indicators.append("Reference has very low entropy")
            risk_score += 0.2
        
        # Check for all numeric or all alpha
        if ref.isdigit() and len(ref) > 8:
            indicators.append("Reference is all numeric (suspicious for long references)")
            risk_score += 0.1
        
        if ref.isalpha() and len(ref) > 6:
            indicators.append("Reference is all alphabetic (unusual)")
            risk_score += 0.1
        
        # Check for keyboard patterns
        if self._has_keyboard_pattern(ref):
            indicators.append("Reference contains keyboard patterns")
            risk_score += 0.15
        
        return min(1.0, risk_score), indicators
    
    def _has_repeated_digits(self, number_str: str) -> bool:
        """
        Check if number has suspicious repeated digit patterns
        """
        if len(number_str) < 3:
            return False
        
        # Check for 3+ consecutive identical digits
        for i in range(len(number_str) - 2):
            if number_str[i] == number_str[i+1] == number_str[i+2]:
                return True
        
        return False
    
    def _has_sequential_pattern(self, text: str) -> bool:
        """
        Check for sequential patterns in text
        """
        if len(text) < 3:
            return False
        
        # Check for sequential numbers
        digits = ''.join(c for c in text if c.isdigit())
        if len(digits) >= 3:
            for i in range(len(digits) - 2):
                try:
                    if int(digits[i+1]) == int(digits[i]) + 1 and int(digits[i+2]) == int(digits[i]) + 2:
                        return True
                except ValueError:
                    pass
        
        # Check for sequential letters
        letters = ''.join(c for c in text if c.isalpha()).upper()
        if len(letters) >= 3:
            for i in range(len(letters) - 2):
                if ord(letters[i+1]) == ord(letters[i]) + 1 and ord(letters[i+2]) == ord(letters[i]) + 2:
                    return True
        
        return False
    
    def _has_keyboard_pattern(self, text: str) -> bool:
        """
        Check for keyboard patterns like QWERTY, ASDF, etc.
        """
        keyboard_patterns = [
            'QWERTY', 'ASDF', 'ZXCV', 'QWER', 'ASDFG', 'ZXCVB',
            '123456', '1234', '234567', '345678'
        ]
        
        text_upper = text.upper()
        for pattern in keyboard_patterns:
            if pattern in text_upper:
                return True
        
        return False
    
    def _is_valid_bic_structure(self, bic: str) -> bool:
        """
        Validate BIC code structure
        """
        if not bic or len(bic) not in [8, 11]:
            return False
        
        # Bank code (4 letters)
        if not bic[:4].isalpha() or not bic[:4].isupper():
            return False
        
        # Country code (2 letters)
        if not bic[4:6].isalpha() or not bic[4:6].isupper():
            return False
        
        # Location code (2 alphanumeric)
        if not bic[6:8].isalnum() or not bic[6:8].isupper():
            return False
        
        # Branch code (3 alphanumeric, optional)
        if len(bic) == 11:
            if not bic[8:11].isalnum() or not bic[8:11].isupper():
                return False
        
        return True
    
    def _is_valid_value_date(self, value_date: str) -> bool:
        """
        Validate value date format and reasonableness
        """
        if not value_date or len(value_date) != 6 or not value_date.isdigit():
            return False
        
        try:
            # Parse YYMMDD
            year = int(value_date[:2])
            month = int(value_date[2:4])
            day = int(value_date[4:6])
            
            # Basic range checks
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            
            # Convert to full year (assume 20XX for now)
            full_year = 2000 + year
            
            # Check if date is reasonable (not too far in past or future)
            try:
                date_obj = datetime(full_year, month, day)
                now = datetime.now()
                
                # Allow dates from 1 year ago to 1 year in future
                if (now - date_obj).days > 365 or (date_obj - now).days > 365:
                    return False
                
            except ValueError:
                return False
            
        except ValueError:
            return False
        
        return True
    
    def _is_valid_currency(self, currency: str) -> bool:
        """
        Validate currency code
        """
        if not currency or len(currency) != 3 or not currency.isalpha() or not currency.isupper():
            return False
        
        # Common currency codes
        valid_currencies = {
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'SGD', 'HKD',
            'KRW', 'CNY', 'INR', 'BRL', 'MXN', 'ZAR', 'RUB', 'TRY'
        }
        
        return currency in valid_currencies
    
    def calculate_benford_deviation(self, amounts: List[float]) -> float:
        """
        Calculate deviation from Benford's Law
        """
        if len(amounts) < 10:
            return 0.0
        
        # Extract first digits
        first_digits = []
        for amount in amounts:
            amount_str = str(int(amount)).lstrip('0')
            if amount_str and amount_str[0].isdigit():
                first_digits.append(int(amount_str[0]))
        
        if len(first_digits) < 10:
            return 0.0
        
        # Calculate observed frequencies
        observed_freq = np.zeros(9)
        for digit in first_digits:
            if 1 <= digit <= 9:
                observed_freq[digit - 1] += 1
        
        observed_freq = observed_freq / len(first_digits)
        
        # Benford's Law expected frequencies
        benford_expected = np.array([np.log10(1 + 1/d) for d in range(1, 10)])
        
        # Calculate deviation
        deviation = np.sum(np.abs(observed_freq - benford_expected))
        
        return deviation
