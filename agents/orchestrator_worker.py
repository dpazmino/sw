"""
Orchestrator-Worker Agent Pattern for transaction splitting and processing
"""

from typing import List
from models.swift_message import SWIFTMessage
from config import Config
from agents.workflow_agents.base_agents import Orchestrator, GenericAgent


class OrchestratorWorker:
    """
    Orchestrator-Worker pattern implementation for SWIFT transaction processing
    """
    
    def __init__(self):
        self.config = Config()
        self.orchestrator = Orchestrator()
    
    def process_transactions(self, messages: List[SWIFTMessage]):
        """
        Main orchestrator method - coordinates workers to process transactions
        """

        prompt = self.orchestrator.create_prompt(messages)

        tasks = self.orchestrator.respond(prompt)

        for task in tasks['tasks']:
            print(GenericAgent().respond(task, tasks['analysis'], messages))

