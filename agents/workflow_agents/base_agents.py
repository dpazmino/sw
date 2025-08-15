
from services.llm_service import LLMService
from config import Config
from models.swift_message import SWIFTMessage
from typing import Dict, List, Tuple, Any
import json


#TODO All the agent classes share common features.  Create an abstract class called BaseAgent so that 
# the other classes can inherit from them.

class SwiftCorrectionAgent:
    
    def __init__(self):
        self.config = Config()

        #TODO  Define LLMService
        #self.llm_service 
        
    def create_prompt(self, message: SWIFTMessage, errors: List[str], corrections: str )-> str:
        """
        Create prompt for LLM correction
        """
        prompt = f"""
You are a SWIFT message validation expert. Please help correct the following SWIFT message:

{message}

by looking at the errors found

{chr(10).join(f"- {error}" for error in errors)}

and implementing the following corrections

{corrections}

Please provide corrections for these errors in place while maintaining the business intent of the transaction.

For missing fields, please add the fields to the message with the correction.


"""
        return prompt
    
    def respond(self, prompt: str) -> Dict[str, Any]:
        """
        Get SWIFT message corrections from LLM
        """
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SWIFT message validation expert. "
                    "Your task is to correct SWIFT message format errors while "
                    "maintaining the business intent of the transaction. "
                    "Respond with JSON containing the corrected fields."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            #TODO  What is the respons format here.  If you follow the code that leads to here, you will see that
            # a particular format is needed to convert the reponst back to a SWIFT message.
            #response_format=
            temperature=0
        )
        
        #TODO  As seen above, what is the result from the response
        #result = 
        
        return result
            
class SwiftEvalutionAgent:
    
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()
        
    def create_prompt(self, message: SWIFTMessage) -> str:
        """
        Create prompt for LLM correction
        """

        #TODO Add a required field below.  This process is mimicing the idea of self-correcting SWIFT messages.
        # You must also add the required field to the SWiFT Message.
        prompt = f"""

Please help list the errors for the following message based only on the rules below.

{message}


Rules:

1.  The message must contain these required fields.

    "required_fields": ["message_type", "reference", "amount", "sender_bic", "receiver_bic", "note"],

    if a required field is missing, please return :

    "Required field <field_name> is missing or empty"

2.  Ignore any problems with any BIC.


Please include corrections under a corrections section in the reponse.

There do not have to be any errors.  If no errors exist, return and empty list in the error section and an empty list in the corrections section.

Return only the errors section and the corrections section.
"""
        return prompt
    
    def respond(self, prompt: str) -> Dict[str, Any]:
        """
        Get SWIFT message corrections from LLM
        """
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SWIFT message validation expert. "
                    "Your task is to correct SWIFT message format errors while "
                    "maintaining the business intent of the transaction. "
                    "Respond with JSON containing the corrected fields. Return all errors in a a label called errors."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result = json.loads(response.choices[0].message.content or "{}")
        
        return result
    
class FraudAmountDetectionAgent:
    
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()
        
    def create_prompt(self, message: SWIFTMessage)-> str:
        """
        Create prompt for LLM correction
        """
        prompt = f"""

Please grade the following SWIFT message for fraud using the rules below.

{message}

Rules 

Rule 1.  if the amount > 10000 this reflects a very high amount and has risk. Add .3 to total risk score
Rule 2.  if amount >= 5000 and amount % 1000 == 0.  This Round amount suggesting structuring: $<amount> and add .2 to total risk score
Rule 3.  if amount > 100000 and the decimal part of the amount is not 00 or 50.  This is unusual precision for large amount and add .1 to total risk score.

Please return your evaluation of the risk according to the rules plus the total risk score.

"""
        return prompt
    
    def respond(self, prompt: str) -> Dict[str, Any]:
        """
        Get SWIFT message corrections from LLM
        """
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SWIFT message fraud detection expert. "
                    "Your task is to investigate SWIFT messages for possibilities of fraud"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "text"},
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        return result
    
class FraudPatternDetectionAgent:
    
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()
        
    def create_prompt(self, message: SWIFTMessage)-> str:
        """
        Create prompt for LLM correction
        """
        prompt = f"""

Please grade the following SWIFT message for fraud using the rules below to detect risk risky fraud patterns.

{message}

Rules 

These are high risk patterns  'TEST.*', 'FAKE.*', 'DEMO.*', '.*999.*', '.*000000.*'
Rule 1.  if the sender bic or the receiver bic contain any of the high risk patterns, this suggests fraud and add .3 to total risk score.
Rule 2.  If the sender bic and the receiver bic are the same, this can be fraud and add a .2 to the total risk score.
Rule 3.  If any words are misspelled, that could be fraud and add a .1 to the total risk score.

Please return your evaluation of the risk according to the rules plus the total risk score.

"""
        return prompt
    
    def respond(self, prompt: str) -> Dict[str, Any]:
        """
        Get SWIFT message corrections from LLM
        """
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SWIFT message fraud detection expert. "
                    "Your task is to investigate SWIFT messages for possibilities of fraud"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "text"},
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        return result
    
class FraudAggAgent:
    
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()
        
    def create_prompt(self, message: SWIFTMessage) -> str:
        """
        Create prompt for LLM correction
        """
        prompt = f"""

Please review the following messages and tell me if a Swift transaction with these messages is fraudulent or not.

{message}

Please response in json format with "thought" that contains the final review and "total_fraud_score" which contains your assessment from 1 to 100
on what you think the fraud score should be.  100 being highest. 

"""
        return prompt
    
    def respond(self, prompt: str) -> Dict[str, Any]:
        """
        Get SWIFT message corrections from LLM
        """
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SWIFT fraud supervisor"
                               "Your job is to make sure no fraudulent SWIFT transactions get processed."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result = json.loads(response.choices[0].message.content or "{}")
         
        return result
    
class Orchestrator:
    
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()
        
    #TODO  create a prompt that deals with reports on high risk transactions.
    #def create_prompt_high_risk(self, message: List[SWIFTMessage]) -> str:
    #  add the prompt.

    
    def create_prompt(self, messages: List[SWIFTMessage]) -> str:
        """
        Create prompt for Orchestration
        """
        prompt = f"""

You are a SWIFT Transaction processor.  You have this list of messages.

{messages}

Your job is to analyze these messages and process them. Only concern your self with amounts, countries, debits and credits.

Do not concern yourself with fraud or compliance.

One of the tasks should be a report for amounts by country and currency.

Please break down the plan into sub plans and tasks.

Return your response in the following format, with an <analysis> section and a <tasks> section.

<analysis>
Provide a high-level summary.
</analysis>

<tasks>
Provide four tasks to process these transactions. Each task must have a <type> and a <description>.
Example task format:
<task>
  <type>compliance report</type>
  <description>Generate a report on the compliance metrics of these messages.</description>
</task>
</tasks>

Respond in JSON Format. 
"""
        return prompt
    
    def respond(self, prompt: str) -> Dict[str, Any]:
        """
        Get SWIFT message corrections from LLM
        """
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result = json.loads(response.choices[0].message.content or "{}")
         
        return result
    
class GenericAgent():
    def __init__(self):
        self.config = Config()
        self.llm_service = LLMService()

    def respond(self, task: str, analysis: str, messages:List[SWIFTMessage] ) -> Dict[str, Any]:
        prompt = f"""
You are a SWIFT payment processor.  Please process the subtasks according to the subtask type and description.

Main Task: {analysis}
Subtask Type: {task['type']}
Subtask Description: {task['description']}

The Swift Messages are here
{messages}

Return 
1.  How the task was processed and a summary of findings for review.

"""
        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "text"},
            temperature=0
        )
        
        result = response.choices[0].message.content 
         
        return result