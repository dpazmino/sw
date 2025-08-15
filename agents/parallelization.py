"""
Parallelization Agent Pattern for concurrent SWIFT message processing
"""

from typing import List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from models.swift_message import SWIFTMessage
from config import Config
from agents.workflow_agents.base_agents import FraudAmountDetectionAgent, FraudPatternDetectionAgent, FraudAggAgent


class ParallelizationAgent:
    """
    Parallelization pattern implementation for processing multiple SWIFT messages concurrently
    """
    
    def __init__(self):
        self.config = Config()
        self.max_workers = self.config.MAX_WORKERS
        self.batch_size = self.config.BATCH_SIZE
    
    def process_messages_parallel(self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
        """
        Process messages in parallel using threading
        """

        processed_messages = []
        
        for msg in messages:
        
            #TODO What agents will be here.  There are two agents already.  Create a third agent.
            # list_of_agents = []

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit batch processing tasks
                future_to_batch = {
                    executor.submit(self._process_msg, msg, agent): agent_idx
                    for agent_idx, agent in enumerate(list_of_agents)
                }
                
                # Collect results as they complete
                completed_batches = 0
                for future in as_completed(future_to_batch):
                    
                    try:
                        batch_results = future.result()
                        msg.fraud_statements.append(batch_results)
                        completed_batches += 1
    
                    except Exception as e:
                        msg.processing_status = "ERROR"
                        msg.validation_errors.append(f"Parallel processing error: {str(e)}")

                processed_messages.append(msg)
            
        return processed_messages
    
    def _process_msg(self, message: SWIFTMessage, fraud_agent) -> List[SWIFTMessage]:
        """
        Process a single messge with one agent
        """
        print(f"Evalutating {message.message_id} for Fraud in Parallel")
        try:
            # Process message through routing agent (includes fraud detection)
            prompt  = fraud_agent.create_prompt(message)
            response = fraud_agent.respond(prompt)
            
        except Exception as e:
            message.processing_status = "ERROR"
            message.validation_errors.append(f"Processing error: {str(e)}")
    
        
        return response
    
    def aggregrate_fraud (self, messages: List[SWIFTMessage]) -> List[SWIFTMessage]:
            """
            Process all fraud messages and denote a message as fraud or not.
            """

            #TODO Add the agent that will aggregrate the messages from the parallelization
            #  fraud_supervior = 

            processed_messages = []
            
            for msg in messages:    
                try:
                    print(f"Aggregrating fraud for {msg.message_id}")
                    prompt = fraud_supervior.create_prompt(msg.fraud_statements)
                    response = fraud_supervior.respond(prompt)

                    #TODO Mark all messages as fraudlent when you have the code working and see what happens in the orchestrator.

                    if response['total_fraud_score'] > 50:
                        msg.mark_as_fraudulent(response['total_score'], response['thought'])
                    msg.fraud_status = "PROCESSED"
                    processed_messages.append(msg)

                except Exception as e:
                    msg.processing_status = "ERROR"
                    msg.validation_errors.append(f"Parallel processing error: {str(e)}")
                    processed_messages.append(msg)
            
            return processed_messages