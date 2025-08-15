"""
Evaluator-Optimizer Agent Pattern for SWIFT message validation and correction
"""

from typing import List, Tuple
from models.swift_message import SWIFTMessage
from services.llm_service import LLMService
from config import Config
from agents.workflow_agents.base_agents import SwiftCorrectionAgent, SwiftEvalutionAgent
import json

class EvaluatorOptimizer:
    """
    Evaluator-Optimizer pattern implementation for SWIFT message validation.
    Validates messages against SWIFT standards and attempts corrections if needed.
    """
    
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()
        self.swift_correction_agent = SwiftCorrectionAgent()
        self.swift_evaluation_agent = SwiftEvalutionAgent()
        self.max_iterations = 3  # Maximum correction attempts
    
    def process_message(self, message: SWIFTMessage) -> SWIFTMessage:
        """
        Main processing method using evaluator-optimizer pattern
        """
        
        iteration = 0
        current_message = message.copy(deep=True)
        
        while iteration < self.max_iterations:
            # Evaluation phase
            current_message = current_message.model_dump_json(indent=2)
            is_valid, errors, corrections = self._evaluate_message(current_message)
            
            if is_valid:
                current_message = SWIFTMessage(**json.loads(current_message))
                current_message.validation_status = "VALID"
                break
            
            try:
                # Optimization phase
                if iteration < self.max_iterations - 1:
                    current_message = self._optimize_message(current_message, errors, corrections)
                    current_message = SWIFTMessage(**current_message)
                else:
                    # Max iterations reached, mark as invalid
                    current_message = SWIFTMessage(**json.loads(current_message))
                    current_message.validation_status = "INVALID"
                    current_message.validation_errors.extend(errors)
            except:
                current_message = message
                current_message.validation_status = "INVALID"
            
            iteration += 1
        
        return current_message
    
    def _evaluate_message(self, message: json) -> Tuple[bool, List[str]]:
        """
        Evaluate SWIFT message against standards
        """
        
        # Basic field validation
        prompt = self.swift_evaluation_agent.create_prompt(message)
        validation_result = self.swift_evaluation_agent.respond(prompt)
        
        is_valid = len(validation_result['errors']) == 0
        
        return is_valid, validation_result['errors'], validation_result['corrections']
    
    def _optimize_message(self, message: SWIFTMessage, errors: List[str], corrections: str) -> SWIFTMessage:
        """
        Attempt to correct message using LLM assistance
        """
        try:
            # Create correction prompt
            prompt = self.swift_correction_agent.create_prompt(message, errors, corrections)
            
            # Get LLM suggestions
            corrected_message = self.swift_correction_agent.respond(prompt)
            
            return corrected_message
            
        except Exception as e:
            # Return original message if correction fails
            message.processing_status = "ERROR"
            message.validation_errors.append(f"Processing in optimizing message: {str(e)}")
            return message
    
