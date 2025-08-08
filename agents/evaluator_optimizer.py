"""
Evaluator-Optimizer Agent Pattern for SWIFT message validation and correction
"""

import logging
from typing import Dict, List, Tuple
from models.swift_message import SWIFTMessage
from services.llm_service import LLMService
from utils.validators import SWIFTValidator
from config import Config


class EvaluatorOptimizer:
    """
    Evaluator-Optimizer pattern implementation for SWIFT message validation.
    Validates messages against SWIFT standards and attempts corrections if needed.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.validator = SWIFTValidator()
        self.llm_service = LLMService()
        self.max_iterations = 3  # Maximum correction attempts
    
    def process_message(self, message: SWIFTMessage) -> SWIFTMessage:
        """
        Main processing method using evaluator-optimizer pattern
        """
        self.logger.debug(f"Processing message {message.message_id} with Evaluator-Optimizer")
        
        iteration = 0
        current_message = message.copy(deep=True)
        
        while iteration < self.max_iterations:
            # Evaluation phase
            is_valid, errors = self._evaluate_message(current_message)
            
            if is_valid:
                current_message.validation_status = "VALID"
                self.logger.debug(f"Message {message.message_id} validated successfully in {iteration + 1} iterations")
                break
            
            # Optimization phase
            if iteration < self.max_iterations - 1:
                self.logger.debug(f"Message {message.message_id} has errors, attempting correction (iteration {iteration + 1})")
                current_message = self._optimize_message(current_message, errors)
            else:
                # Max iterations reached, mark as invalid
                current_message.validation_status = "INVALID"
                current_message.validation_errors.extend(errors)
                self.logger.warning(f"Message {message.message_id} could not be corrected after {self.max_iterations} iterations")
            
            iteration += 1
        
        return current_message
    
    def _evaluate_message(self, message: SWIFTMessage) -> Tuple[bool, List[str]]:
        """
        Evaluate SWIFT message against standards
        """
        errors = []
        
        # Basic field validation
        validation_result = self.validator.validate_swift_message(message)
        if not validation_result.is_valid:
            errors.extend(validation_result.errors)
        
        # Business rule validation
        business_errors = self._validate_business_rules(message)
        errors.extend(business_errors)
        
        # Format validation
        format_errors = self._validate_format(message)
        errors.extend(format_errors)
        
        is_valid = len(errors) == 0
        
        self.logger.debug(f"Message {message.message_id} evaluation: {'VALID' if is_valid else 'INVALID'} ({len(errors)} errors)")
        
        return is_valid, errors
    
    def _optimize_message(self, message: SWIFTMessage, errors: List[str]) -> SWIFTMessage:
        """
        Attempt to correct message using LLM assistance
        """
        try:
            # Create correction prompt
            prompt = self._create_correction_prompt(message, errors)
            
            # Get LLM suggestions
            correction_response = self.llm_service.get_swift_correction(prompt)
            
            # Apply corrections
            corrected_message = self._apply_corrections(message, correction_response)
            
            self.logger.debug(f"Applied corrections to message {message.message_id}")
            return corrected_message
            
        except Exception as e:
            self.logger.error(f"Error during message optimization: {str(e)}")
            # Return original message if correction fails
            return message
    
    def _validate_business_rules(self, message: SWIFTMessage) -> List[str]:
        """
        Validate business rules specific to SWIFT messages
        """
        errors = []
        
        # Amount validation
        try:
            amount = float(message.amount)
            if amount > self.config.SWIFT_STANDARDS["max_amount"]:
                errors.append(f"Amount {amount} exceeds maximum allowed {self.config.SWIFT_STANDARDS['max_amount']}")
            if amount < self.config.SWIFT_STANDARDS["min_amount"]:
                errors.append(f"Amount {amount} below minimum allowed {self.config.SWIFT_STANDARDS['min_amount']}")
        except ValueError:
            errors.append("Invalid amount format")
        
        # BIC validation
        if not self._validate_bic_format(message.sender_bic):
            errors.append(f"Invalid sender BIC format: {message.sender_bic}")
        
        if not self._validate_bic_format(message.receiver_bic):
            errors.append(f"Invalid receiver BIC format: {message.receiver_bic}")
        
        # Same sender/receiver validation
        if message.sender_bic == message.receiver_bic:
            errors.append("Sender and receiver BIC cannot be the same")
        
        # Reference length validation
        if len(message.reference) > self.config.SWIFT_STANDARDS["max_reference_length"]:
            errors.append(f"Reference length {len(message.reference)} exceeds maximum {self.config.SWIFT_STANDARDS['max_reference_length']}")
        
        return errors
    
    def _validate_format(self, message: SWIFTMessage) -> List[str]:
        """
        Validate SWIFT message format requirements
        """
        errors = []
        
        # Message type validation
        if message.message_type not in self.config.SWIFT_STANDARDS["valid_message_types"]:
            errors.append(f"Invalid message type: {message.message_type}")
        
        # Currency code validation
        if len(message.currency) != 3 or not message.currency.isalpha():
            errors.append(f"Invalid currency code: {message.currency}")
        
        # Value date validation (YYMMDD format)
        if len(message.value_date) != 6 or not message.value_date.isdigit():
            errors.append(f"Invalid value date format: {message.value_date}")
        
        return errors
    
    def _validate_bic_format(self, bic: str) -> bool:
        """
        Validate BIC code format
        """
        if not bic or len(bic) not in [8, 11]:
            return False
        
        # Bank code (4 letters)
        if not bic[:4].isalpha():
            return False
        
        # Country code (2 letters)
        if not bic[4:6].isalpha():
            return False
        
        # Location code (2 alphanumeric)
        if not bic[6:8].isalnum():
            return False
        
        # Branch code (3 alphanumeric, optional)
        if len(bic) == 11 and not bic[8:11].isalnum():
            return False
        
        return True
    
    def _create_correction_prompt(self, message: SWIFTMessage, errors: List[str]) -> str:
        """
        Create prompt for LLM correction
        """
        prompt = f"""
You are a SWIFT message validation expert. Please help correct the following SWIFT message:

Message Type: {message.message_type}
Reference: {message.reference}
Amount: {message.amount}
Currency: {message.currency}
Sender BIC: {message.sender_bic}
Receiver BIC: {message.receiver_bic}
Value Date: {message.value_date}

Validation Errors Found:
{chr(10).join(f"- {error}" for error in errors)}

Please provide corrections for these errors while maintaining the business intent of the transaction.
Focus on format corrections, BIC code fixes, and ensuring compliance with SWIFT standards.

Respond with corrected values in JSON format:
{{
    "reference": "corrected_reference",
    "amount": "corrected_amount",
    "sender_bic": "corrected_sender_bic",
    "receiver_bic": "corrected_receiver_bic",
    "value_date": "corrected_value_date",
    "corrections_made": ["list of corrections applied"]
}}
"""
        return prompt
    
    def _apply_corrections(self, message: SWIFTMessage, correction_response: Dict) -> SWIFTMessage:
        """
        Apply LLM corrections to the message
        """
        corrected_message = message.copy(deep=True)
        
        # Apply corrections if provided
        if "reference" in correction_response:
            corrected_message.reference = correction_response["reference"][:16]  # Ensure max length
        
        if "amount" in correction_response:
            corrected_message.amount = correction_response["amount"]
        
        if "sender_bic" in correction_response:
            corrected_message.sender_bic = correction_response["sender_bic"]
        
        if "receiver_bic" in correction_response:
            corrected_message.receiver_bic = correction_response["receiver_bic"]
        
        if "value_date" in correction_response:
            corrected_message.value_date = correction_response["value_date"]
        
        # Log corrections made
        if "corrections_made" in correction_response:
            self.logger.info(f"Applied corrections to message {message.message_id}: {correction_response['corrections_made']}")
        
        return corrected_message
