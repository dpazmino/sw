"""
Parallelization Agent Pattern for concurrent SWIFT message processing
"""

import logging
from typing import List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from models.swift_message import SWIFTMessage
from config import Config


class ParallelizationAgent:
    """
    Parallelization pattern implementation for processing multiple SWIFT messages concurrently
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.max_workers = self.config.MAX_WORKERS
        self.batch_size = self.config.BATCH_SIZE
    
    def process_messages_parallel(self, messages: List[SWIFTMessage], routing_agent) -> List[SWIFTMessage]:
        """
        Process messages in parallel using threading
        """
        self.logger.info(f"Starting parallel processing of {len(messages)} messages with {self.max_workers} workers")
        
        start_time = time.time()
        processed_messages = []
        
        # Split messages into batches for better resource management
        batches = self._create_batches(messages, self.batch_size)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch processing tasks
            future_to_batch = {
                executor.submit(self._process_batch, batch, routing_agent): batch_idx
                for batch_idx, batch in enumerate(batches)
            }
            
            # Collect results as they complete
            completed_batches = 0
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                
                try:
                    batch_results = future.result()
                    processed_messages.extend(batch_results)
                    completed_batches += 1
                    
                    self.logger.info(f"Completed batch {batch_idx + 1}/{len(batches)} ({completed_batches * self.batch_size} messages)")
                    
                except Exception as e:
                    self.logger.error(f"Error processing batch {batch_idx}: {str(e)}")
                    # Add original messages with error status
                    for msg in batches[batch_idx]:
                        msg.processing_status = "ERROR"
                        msg.validation_errors.append(f"Parallel processing error: {str(e)}")
                        processed_messages.append(msg)
        
        processing_time = time.time() - start_time
        self.logger.info(f"Parallel processing completed in {processing_time:.2f} seconds")
        
        return processed_messages
    
    def _create_batches(self, messages: List[SWIFTMessage], batch_size: int) -> List[List[SWIFTMessage]]:
        """
        Split messages into batches for parallel processing
        """
        batches = []
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batches.append(batch)
        
        self.logger.debug(f"Created {len(batches)} batches of size {batch_size}")
        return batches
    
    def _process_batch(self, batch: List[SWIFTMessage], routing_agent) -> List[SWIFTMessage]:
        """
        Process a single batch of messages
        """
        batch_start_time = time.time()
        processed_batch = []
        
        for message in batch:
            try:
                # Process message through routing agent (includes fraud detection)
                processed_message = routing_agent.route_message(message)
                processed_message.processing_status = "PROCESSED"
                processed_batch.append(processed_message)
                
            except Exception as e:
                self.logger.error(f"Error processing message {message.message_id}: {str(e)}")
                message.processing_status = "ERROR"
                message.validation_errors.append(f"Processing error: {str(e)}")
                processed_batch.append(message)
        
        batch_time = time.time() - batch_start_time
        self.logger.debug(f"Processed batch of {len(batch)} messages in {batch_time:.2f} seconds")
        
        return processed_batch
    
    def process_with_custom_function(self, messages: List[SWIFTMessage], 
                                   processing_function: Callable[[SWIFTMessage], SWIFTMessage]) -> List[SWIFTMessage]:
        """
        Process messages in parallel using a custom processing function
        """
        self.logger.info(f"Starting parallel processing with custom function for {len(messages)} messages")
        
        start_time = time.time()
        processed_messages = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit individual message processing tasks
            future_to_message = {
                executor.submit(self._safe_process_message, message, processing_function): message
                for message in messages
            }
            
            # Collect results
            completed_count = 0
            for future in as_completed(future_to_message):
                original_message = future_to_message[future]
                
                try:
                    processed_message = future.result()
                    processed_messages.append(processed_message)
                    completed_count += 1
                    
                    if completed_count % 100 == 0:
                        self.logger.info(f"Processed {completed_count}/{len(messages)} messages")
                        
                except Exception as e:
                    self.logger.error(f"Error processing message {original_message.message_id}: {str(e)}")
                    original_message.processing_status = "ERROR"
                    original_message.validation_errors.append(f"Custom processing error: {str(e)}")
                    processed_messages.append(original_message)
        
        processing_time = time.time() - start_time
        self.logger.info(f"Custom parallel processing completed in {processing_time:.2f} seconds")
        
        return processed_messages
    
    def _safe_process_message(self, message: SWIFTMessage, 
                            processing_function: Callable[[SWIFTMessage], SWIFTMessage]) -> SWIFTMessage:
        """
        Safely process a single message with error handling
        """
        try:
            return processing_function(message)
        except Exception as e:
            self.logger.error(f"Error in custom processing function for message {message.message_id}: {str(e)}")
            message.processing_status = "ERROR"
            message.validation_errors.append(f"Custom function error: {str(e)}")
            return message
    
    def get_processing_stats(self, messages: List[SWIFTMessage]) -> dict:
        """
        Calculate processing statistics
        """
        total_messages = len(messages)
        processed_count = sum(1 for msg in messages if msg.processing_status == "PROCESSED")
        error_count = sum(1 for msg in messages if msg.processing_status == "ERROR")
        pending_count = sum(1 for msg in messages if msg.processing_status == "PENDING")
        
        stats = {
            "total_messages": total_messages,
            "processed_count": processed_count,
            "error_count": error_count,
            "pending_count": pending_count,
            "success_rate": (processed_count / total_messages * 100) if total_messages > 0 else 0,
            "error_rate": (error_count / total_messages * 100) if total_messages > 0 else 0
        }
        
        return stats
