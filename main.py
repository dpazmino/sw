"""
SWIFT Transaction Processing System with Agent Patterns
Main application entry point
"""

import logging
import time
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from models.swift_message import SWIFTMessage
from services.swift_generator import SWIFTGenerator
from services.database import DatabaseService
from agents.evaluator_optimizer import EvaluatorOptimizer
from agents.parallelization import ParallelizationAgent
from agents.routing import RoutingAgent
from agents.orchestrator_worker import OrchestratorWorker
from agents.prompt_chaining import PromptChainingAgent
from agents.transaction_analyzer import TransactionAnalyzer
from utils.logger import setup_logger


class SWIFTProcessingSystem:
    """Main system orchestrating all agent patterns for SWIFT processing"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger(__name__)
        self.db_service = DatabaseService()
        self.swift_generator = SWIFTGenerator()
        
        # Initialize agent patterns
        self.evaluator_optimizer = EvaluatorOptimizer()
        self.parallelization_agent = ParallelizationAgent()
        self.routing_agent = RoutingAgent()
        self.orchestrator_worker = OrchestratorWorker()
        self.prompt_chaining_agent = PromptChainingAgent()
        self.transaction_analyzer = TransactionAnalyzer()
        
        self.logger.info("SWIFT Processing System initialized")
    
    def generate_swift_messages(self) -> List[SWIFTMessage]:
        """Generate 1000 SWIFT messages across 30 banks"""
        self.logger.info("Generating 1000 SWIFT messages across 30 banks...")
        
        start_time = time.time()
        messages = self.swift_generator.generate_messages(
            count=self.config.MESSAGE_COUNT,
            bank_count=self.config.BANK_COUNT
        )
        
        generation_time = time.time() - start_time
        self.logger.info(f"Generated {len(messages)} SWIFT messages in {generation_time:.2f} seconds")
        
        return messages
    
    def process_with_evaluator_optimizer(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """Step 1: Validate and correct SWIFT messages using Evaluator-Optimizer pattern"""
        self.logger.info("Step 1: Processing messages with Evaluator-Optimizer pattern...")
        
        validated_messages = []
        start_time = time.time()
        
        for i, message in enumerate(messages):
            if i % 100 == 0:
                self.logger.info(f"Processed {i}/{len(messages)} messages")
            
            validated_message = self.evaluator_optimizer.process_message(message)
            validated_messages.append(validated_message)
        
        processing_time = time.time() - start_time
        self.logger.info(f"Evaluator-Optimizer completed in {processing_time:.2f} seconds")
        
        return validated_messages
    
    def process_with_parallelization(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """Step 2: Process messages in parallel with fraud detection routing"""
        self.logger.info("Step 2: Processing messages with Parallelization and Routing patterns...")
        
        start_time = time.time()
        processed_messages = self.parallelization_agent.process_messages_parallel(
            messages, 
            self.routing_agent
        )
        
        processing_time = time.time() - start_time
        self.logger.info(f"Parallelization completed in {processing_time:.2f} seconds")
        
        # Update database with processed messages
        self.db_service.update_transactions(processed_messages)
        
        return processed_messages
    
    def process_with_prompt_chaining(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """Step 3: Enhanced fraud analysis using Prompt Chaining pattern"""
        self.logger.info("Step 3: Processing with Prompt Chaining pattern...")
        
        start_time = time.time()
        
        # Select high-risk transactions for detailed prompt chain analysis
        high_risk_messages = [msg for msg in messages if hasattr(msg, 'fraud_score') and float(getattr(msg, 'fraud_score', 0)) > 0.3]
        
        if high_risk_messages:
            self.logger.info(f"Running prompt chain analysis on {len(high_risk_messages)} high-risk transactions")
            
            # Prepare data for prompt chaining
            fraud_scores = [float(getattr(msg, 'fraud_score', 0)) for msg in high_risk_messages]
            fraud_indicators = [getattr(msg, 'fraud_indicators', []) for msg in high_risk_messages]
            
            # Run prompt chain analysis
            chain_results = self.prompt_chaining_agent.batch_process_with_chaining(
                high_risk_messages, fraud_scores, fraud_indicators
            )
            
            # Update messages with chain analysis results
            for i, result in enumerate(chain_results):
                if i < len(high_risk_messages):
                    msg = high_risk_messages[i]
                    # Add chain analysis results to the message
                    setattr(msg, 'chain_analysis', result.get('chain_analysis', {}))
                    setattr(msg, 'agent_perspectives', result.get('agent_perspectives', {}))
                    
                    # Update fraud status based on chain decision
                    final_decision = result.get('chain_analysis', {}).get('final_decision', 'HOLD')
                    if final_decision == "REJECT":
                        msg.fraud_status = "FRAUDULENT"
                    elif final_decision == "HOLD":
                        msg.fraud_status = "HELD"
                    elif final_decision == "APPROVE":
                        msg.fraud_status = "CLEAN"
        
        processing_time = time.time() - start_time
        self.logger.info(f"Prompt Chaining completed in {processing_time:.2f} seconds")
        
        return messages
    
    def process_with_orchestrator_worker(self, messages: List[SWIFTMessage]) -> None:
        """Step 4: Split transactions using Orchestrator-Worker pattern"""
        self.logger.info("Step 4: Processing with Orchestrator-Worker pattern...")
        
        start_time = time.time()
        
        # Filter non-fraudulent messages for final processing
        clean_messages = [msg for msg in messages if msg.fraud_status != "FRAUDULENT"]
        
        self.orchestrator_worker.process_transactions(clean_messages)
        
        processing_time = time.time() - start_time
        self.logger.info(f"Orchestrator-Worker completed in {processing_time:.2f} seconds")
    
    def generate_statistics(self, messages: List[SWIFTMessage]) -> dict:
        """Generate processing statistics"""
        total_messages = len(messages)
        fraudulent_count = sum(1 for msg in messages if msg.fraud_status == "FRAUDULENT")
        held_count = sum(1 for msg in messages if msg.fraud_status == "HELD")
        processed_count = sum(1 for msg in messages if msg.fraud_status == "CLEAN")
        
        total_amount = sum(float(msg.amount) for msg in messages)
        avg_amount = total_amount / total_messages if total_messages > 0 else 0
        
        banks_involved = len(set(msg.sender_bic for msg in messages))
        
        stats = {
            "total_messages": total_messages,
            "fraudulent_count": fraudulent_count,
            "held_count": held_count,
            "processed_count": processed_count,
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "banks_involved": banks_involved,
            "fraud_rate": (fraudulent_count / total_messages) * 100 if total_messages > 0 else 0
        }
        
        return stats
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("Starting SWIFT Transaction Processing System")
            overall_start_time = time.time()
            
            # Initialize database
            self.db_service.initialize_database()
            
            # Step 1: Generate SWIFT messages
            messages = self.generate_swift_messages()
            
            # Step 2: Evaluator-Optimizer pattern
            validated_messages = self.process_with_evaluator_optimizer(messages)
            
            # Step 3: Parallelization with Routing pattern
            processed_messages = self.process_with_parallelization(validated_messages)
            
            # Step 4: Prompt Chaining pattern for enhanced fraud analysis
            chain_analyzed_messages = self.process_with_prompt_chaining(processed_messages)
            
            # Step 5: Orchestrator-Worker pattern
            self.process_with_orchestrator_worker(chain_analyzed_messages)
            
            # Generate and display statistics
            stats = self.generate_statistics(chain_analyzed_messages)
            
            overall_time = time.time() - overall_start_time
            
            self.logger.info("=== PROCESSING COMPLETE ===")
            self.logger.info(f"Total execution time: {overall_time:.2f} seconds")
            self.logger.info(f"Messages processed: {stats['total_messages']}")
            self.logger.info(f"Fraudulent transactions: {stats['fraudulent_count']} ({stats['fraud_rate']:.2f}%)")
            self.logger.info(f"Held for review: {stats['held_count']}")
            self.logger.info(f"Successfully processed: {stats['processed_count']}")
            self.logger.info(f"Total amount processed: ${stats['total_amount']:,.2f}")
            self.logger.info(f"Average transaction amount: ${stats['average_amount']:,.2f}")
            self.logger.info(f"Banks involved: {stats['banks_involved']}")
            
        except Exception as e:
            self.logger.error(f"System error: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    system = SWIFTProcessingSystem()
    system.run()
