"""
SWIFT Transaction Processing System with Agent Patterns
Main application entry point
"""

from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from models.swift_message import SWIFTMessage
from services.swift_generator import SWIFTGenerator
from agents.evaluator_optimizer import EvaluatorOptimizer
from agents.parallelization import ParallelizationAgent
from agents.orchestrator_worker import OrchestratorWorker
from agents.prompt_chaining import PromptChainingAgent


class SWIFTProcessingSystem:
    """Main system orchestrating all agent patterns for SWIFT processing"""
    
    def __init__(self):
        self.config = Config()
        self.swift_generator = SWIFTGenerator()
        
        # Initialize agent patterns
        self.evaluator_optimizer = EvaluatorOptimizer()
        self.parallelization_agent = ParallelizationAgent()
        self.orchestrator_worker = OrchestratorWorker()
        self.prompt_chaining_agent = PromptChainingAgent()
    
    def generate_swift_messages(self) -> List[SWIFTMessage]:
        """Generate 1000 SWIFT messages across 30 banks"""

        messages = self.swift_generator.generate_messages(
            count=self.config.MESSAGE_COUNT,
            bank_count=self.config.BANK_COUNT
        )
        
        return messages
    
    def process_with_evaluator_optimizer(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """Step 1: Validate and correct SWIFT messages using Evaluator-Optimizer pattern"""
        
        validated_messages = []
        
        for message in messages:
            print(f"Evaluating and optimizing message {message.message_id}")
            validated_message = self.evaluator_optimizer.process_message(message)
            validated_messages.append(validated_message)
        
        return validated_messages
    
    def process_with_parallelization(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """Step 2: Process messages in parallel with fraud detection routing"""
        
        fraud_messages = self.parallelization_agent.process_messages_parallel(
            messages 
        )
        
        processed_messages = self.parallelization_agent.aggregrate_fraud(
            fraud_messages 
        )
        
        return processed_messages
    
    def process_with_prompt_chaining(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """Step 3: Enhanced fraud analysis using Prompt Chaining pattern"""
        
        results = []
        for message in messages:
            print(f"Processing {message.message_id} in the transaction chain")
            chain_results = self.prompt_chaining_agent.analyze_transaction_chain(
                message
            )
            results.append(chain_results)
        
        return results
    
    def process_with_orchestrator_worker(self, messages: List[SWIFTMessage]) -> None:
        """Step 4: Split transactions using Orchestrator-Worker pattern"""
        
        # Filter non-fraudulent messages for final processing
        #TODO  You can change clean messages and get a different result in the task output.
        # The reports will be printed to the console.  Run one set of messages that are not fraudulent
        #  and then change the message structure so that a whole new set of reports are created.
        #  sumbmit both sets of reports.
        clean_messages = [msg for msg in messages if msg.fraud_status != "FRAUDULENT"]
        
        self.orchestrator_worker.process_transactions(clean_messages)
        
    
    def run(self):
        """Main execution method"""
        try:
            
            # Initialize database
            # self.db_service.initialize_database()
            
            # Step 1: Generate SWIFT messages
            messages = self.generate_swift_messages()
            
            # Step 2: Evaluator-Optimizer pattern
            #TODO  call the evaluator optimizer and save result in a variable.
            
            # Step 3: Parallelization 
            #TODO Call the parallelization process and pass in the results from the previous step
            
            # Step 4: Prompt Chaining pattern for enhanced fraud analysis
            #TODO Call the prompt chaining and pass in the values from parallelization.
            
            # Step 5: Orchestrator-Worker pattern
            #TODO Pass in the results from the previous step to the orchestrator
            #self.process_with_orchestrator_worker(<value>)
            
        except Exception as e:
            raise


if __name__ == "__main__":
    system = SWIFTProcessingSystem()
    system.run()
