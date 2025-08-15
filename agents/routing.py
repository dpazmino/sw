"""
Routing Agent Pattern for fraud detection and message routing using Benford's Law
"""

import logging
from typing import List, Dict, Tuple
import numpy as np
from scipy import stats

from models.swift_message import SWIFTMessage
from services.fraud_detection import FraudDetectionService
from services.llm_service import LLMService
from config import Config


class RoutingAgent:
    """
    Routing pattern implementation for SWIFT message fraud detection and routing
    Uses Benford's Law for statistical fraud detection
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.fraud_service = FraudDetectionService()
        self.llm_service = LLMService()
        
        # Benford's Law expected frequencies for first digits 1-9
        self.benford_expected = np.array([
            np.log10(1 + 1/d) for d in range(1, 10)
        ])
        
        self.logger.info("Routing Agent initialized with Benford's Law fraud detection")
    
    def route_message(self, message: SWIFTMessage) -> SWIFTMessage:
        """
        Route message based on fraud detection analysis
        """
        
        # Perform fraud detection
        fraud_score, fraud_indicators = self._detect_fraud(message)
        
        # Route based on fraud score and indicators
        if fraud_score > 0.8:
            return self._route_to_reject(message, fraud_score, fraud_indicators)
        elif fraud_score > self.config.FRAUD_REVIEW_THRESHOLD:
            return self._route_to_llm_review(message, fraud_score, fraud_indicators)
        else:
            return self._route_to_processing(message, fraud_score)
    
    def analyze_batch_with_benfords_law(self, messages: List[SWIFTMessage]) -> Tuple[float, Dict[str, float]]:
        """
        Analyze a batch of messages using Benford's Law to detect systematic fraud
        """
        if len(messages) < 10:
            self.logger.warning("Insufficient messages for Benford's Law analysis")
            return 0.0, {}
        
        # Extract first digits from amounts
        first_digits = []
        for message in messages:
            digit = message.get_first_digit()
            if digit > 0:  # Exclude zero or invalid digits
                first_digits.append(digit)
        
        if len(first_digits) < 10:
            self.logger.warning("Insufficient valid first digits for Benford's Law analysis")
            return 0.0, {}
        
        # Calculate observed frequencies
        observed_freq = np.zeros(9)
        for digit in first_digits:
            observed_freq[digit - 1] += 1
        
        observed_freq = observed_freq / len(first_digits)
        
        # Chi-square test against Benford's Law
        chi_square, p_value = stats.chisquare(observed_freq, self.benford_expected)
        
        # Calculate deviation metrics
        deviation_score = np.sum(np.abs(observed_freq - self.benford_expected))
        
        analysis_results = {
            "chi_square": float(chi_square),
            "p_value": float(p_value),
            "deviation_score": float(deviation_score),
            "sample_size": len(first_digits),
            "significant_deviation": p_value < self.config.BENFORD_THRESHOLD
        }
        
        # Overall fraud probability based on deviation
        fraud_probability = min(1.0, deviation_score * 2)  # Scale deviation to probability
        
        self.logger.info(f"Benford's Law analysis: p-value={p_value:.4f}, deviation={deviation_score:.4f}, fraud_prob={fraud_probability:.4f}")
        
        return fraud_probability, analysis_results
    
    def _detect_fraud(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Perform comprehensive fraud detection on a single message
        """
        fraud_indicators = []
        fraud_scores = []
        
        # Individual transaction analysis
        individual_score, individual_indicators = self.fraud_service.analyze_transaction(message)
        fraud_scores.append(individual_score)
        fraud_indicators.extend(individual_indicators)
        
        # Amount-based analysis
        amount_score, amount_indicators = self._analyze_amount_patterns(message)
        fraud_scores.append(amount_score)
        fraud_indicators.extend(amount_indicators)
        
        # BIC-based analysis
        bic_score, bic_indicators = self._analyze_bic_patterns(message)
        fraud_scores.append(bic_score)
        fraud_indicators.extend(bic_indicators)
        
        # Time-based analysis
        time_score, time_indicators = self._analyze_timing_patterns(message)
        fraud_scores.append(time_score)
        fraud_indicators.extend(time_indicators)
        
        # Calculate combined fraud score (weighted average)
        weights = [0.4, 0.3, 0.2, 0.1]  # Individual, Amount, BIC, Time
        combined_score = np.average(fraud_scores, weights=weights)
        
        self.logger.debug(f"Message {message.message_id} fraud analysis: score={combined_score:.3f}, indicators={len(fraud_indicators)}")
        
        return combined_score, fraud_indicators
    
    def _analyze_amount_patterns(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze amount patterns for fraud indicators
        """
        indicators = []
        score = 0.0
        
        try:
            amount = float(message.amount)
            
            # Round number detection (potential structuring)
            if amount % 1000 == 0 and amount >= 10000:
                indicators.append("Round amount suggests possible structuring")
                score += 0.2
            
            # Unusual precision (too many decimal places for large amounts)
            if amount > 100000 and '.' in message.amount:
                decimal_places = len(message.amount.split('.')[1])
                if decimal_places > 2:
                    indicators.append("Unusual precision for large amount")
                    score += 0.1
            
            # Suspiciously small amounts for international transfers
            if amount < 100:
                indicators.append("Unusually small amount for international transfer")
                score += 0.15
            
            # Very large amounts
            if amount > 1000000:
                indicators.append("Very large transaction amount")
                score += 0.25
            
        except ValueError:
            indicators.append("Invalid amount format")
            score = 0.8
        
        return min(1.0, score), indicators
    
    def _analyze_bic_patterns(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze BIC patterns for fraud indicators
        """
        indicators = []
        score = 0.0
        
        # Check for high-risk countries (simplified example)
        high_risk_countries = ['XX', 'YY', 'ZZ']  # Placeholder codes
        
        sender_country = message.sender_bic[4:6] if len(message.sender_bic) >= 6 else ""
        receiver_country = message.receiver_bic[4:6] if len(message.receiver_bic) >= 6 else ""
        
        if sender_country in high_risk_countries:
            indicators.append(f"Sender from high-risk country: {sender_country}")
            score += 0.3
        
        if receiver_country in high_risk_countries:
            indicators.append(f"Receiver in high-risk country: {receiver_country}")
            score += 0.3
        
        # Check for unusual BIC patterns
        if message.sender_bic == message.receiver_bic:
            indicators.append("Sender and receiver BIC are identical")
            score += 0.5
        
        # Check for test BIC patterns
        if any(test_pattern in message.sender_bic.upper() for test_pattern in ['TEST', 'FAKE', 'DEMO']):
            indicators.append("Sender BIC contains test patterns")
            score += 0.4
        
        if any(test_pattern in message.receiver_bic.upper() for test_pattern in ['TEST', 'FAKE', 'DEMO']):
            indicators.append("Receiver BIC contains test patterns")
            score += 0.4
        
        return min(1.0, score), indicators
    
    def _analyze_timing_patterns(self, message: SWIFTMessage) -> Tuple[float, List[str]]:
        """
        Analyze timing patterns for fraud indicators
        """
        indicators = []
        score = 0.0
        
        # Check for weekend/holiday transactions (simplified)
        # In a real implementation, this would check against a holiday calendar
        
        # Check for rapid-fire transactions (would need transaction history)
        # This is a placeholder for timing-based analysis
        
        # Check value date vs current date
        try:
            import datetime
            current_date = datetime.datetime.now().strftime('%y%m%d')
            value_date = message.value_date
            
            if value_date < current_date:
                days_diff = int(current_date) - int(value_date)
                if days_diff > 30:  # More than 30 days in the past
                    indicators.append("Value date significantly in the past")
                    score += 0.2
            
        except (ValueError, AttributeError):
            indicators.append("Invalid value date format")
            score += 0.1
        
        return min(1.0, score), indicators
    
    def _route_to_reject(self, message: SWIFTMessage, fraud_score: float, indicators: List[str]) -> SWIFTMessage:
        """
        Route message to automatic rejection
        """
        message.mark_as_fraudulent(fraud_score, f"High fraud score: {', '.join(indicators)}")
        self.logger.warning(f"Message {message.message_id} REJECTED - fraud score: {fraud_score:.3f}")
        return message
    
    def _route_to_llm_review(self, message: SWIFTMessage, fraud_score: float, indicators: List[str]) -> SWIFTMessage:
        """
        Route message to LLM for human-like review
        """
        try:
            # Get LLM review
            review_result = self.llm_service.review_suspicious_transaction(message, fraud_score, indicators)
            
            if review_result["decision"] == "APPROVE":
                message.mark_as_clean(fraud_score)
                self.logger.info(f"Message {message.message_id} APPROVED by LLM review")
            else:
                message.mark_as_held(fraud_score, f"LLM review: {review_result['reasoning']}")
                self.logger.info(f"Message {message.message_id} HELD for review")
            
        except Exception as e:
            self.logger.error(f"LLM review failed for message {message.message_id}: {str(e)}")
            message.mark_as_held(fraud_score, f"LLM review failed: {str(e)}")
        
        return message
    
    def _route_to_processing(self, message: SWIFTMessage, fraud_score: float) -> SWIFTMessage:
        """
        Route message to normal processing
        """
        message.mark_as_clean(fraud_score)
        self.logger.debug(f"Message {message.message_id} routed to processing - fraud score: {fraud_score:.3f}")
        return message
