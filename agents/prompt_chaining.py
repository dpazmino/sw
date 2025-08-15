"""
Prompt Chaining Agent for SWIFT Transaction Processing

This agent implements a prompt chaining pattern where multiple AI agents
with different specializations collaborate through conversation to analyze 
SWIFT transactions, creating a more thorough and contextual fraud analysis.
"""

import json
from typing import Dict, Any, List
from datetime import datetime

from openai import OpenAI
from models.swift_message import SWIFTMessage
from config import Config


class PromptChainingAgent:
    """
    Implements prompt chaining pattern for enhanced SWIFT transaction analysis.
    
    This agent creates a conversation between specialized AI agents:
    1. Initial Screener - Fast triage assessment
    2. Technical Analyst - Deep technical validation
    3. Risk Assessor - Risk pattern analysis  
    4. Compliance Officer - Regulatory compliance check
    5. Final Reviewer - Synthesizes all findings
    """
    
    def __init__(self):
        self.config = Config()
        
        # Initialize OpenAI client
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = self.config.OPENAI_MODEL
    
    def analyze_transaction_chain(self, message: SWIFTMessage) -> Dict[str, Any]:
        """
        Main method that runs the complete prompt chain analysis
        """

        chain_results = {}
    
        try:
            # Step 1: Initial Screener
            screener_result = self._run_initial_screener(message)
            chain_results["screener"] = screener_result
            
            # Step 2: 
            #TODO Look at the prompts and see what comes next. Pay attention to what is passed in.
            
            # Step 3: Risk Assessor (uses both previous outputs)
            risk_result = self._run_risk_assessor(message, screener_result, <results from step2>)
            chain_results["risk_assessor"] = risk_result
            
            # Step 4: Compliance Officer (uses all previous context)
            #TODO Look at the prompts and see what comes next. Pay attention to what is passed in.
            # Notice that we are passing in the chain results in the next step.
            
            # Step 5: Final Reviewer (synthesizes all findings)
            final_result = self._run_final_reviewer(message, chain_results)
            chain_results["final_reviewer"] = final_result
            
            # Compile final result
            result = {
                "transaction_id": message.message_id,
                "chain_analysis": {
                    "final_decision": final_result.get("final_decision", "HOLD"),
                    "confidence_score": final_result.get("confidence_score", 0.5),
                    "risk_level": final_result.get("risk_level", "MEDIUM"),
                    "consensus_reasoning": final_result.get("consensus_reasoning", ""),
                    "recommended_actions": final_result.get("recommended_actions", [])
                },
                "agent_perspectives": chain_results,
                "chain_metadata": {
                    "steps_completed": len(chain_results),
                }
            }
            
            setattr(message, 'chain_analysis', result.get('chain_analysis', {}))
            setattr(message, 'agent_perspectives', result.get('agent_perspectives', {}))
            
            # Update fraud status based on chain decision
            final_decision = result.get('chain_analysis', {}).get('final_decision', 'HOLD')

            if final_decision == "REJECT":
                message.fraud_status = "FRAUDULENT"
            elif final_decision == "HOLD":
                message.fraud_status = "HELD"
            elif final_decision == "APPROVE":
                message.fraud_status = "CLEAN"
            
        except Exception as e:
            message.processing_status = "ERROR"
            message.validation_errors.append(f"Chain processing error: {str(e)}")

        return message         
    
    def _run_initial_screener(self, message: SWIFTMessage) -> Dict[str, Any]:
        """Step 1: Initial triage and quick assessment"""
        
        system_prompt = """You are an Initial Transaction Screener with 15+ years experience in SWIFT fraud detection.
        Your role is to quickly triage transactions and flag obvious red flags. You work fast but thoroughly.
        Focus on immediate risk indicators and provide clear direction for deeper analysis."""
        
        user_prompt = f"""
        INITIAL SCREENING ASSESSMENT
        
        Transaction: {message.message_id}
        Type: {message.message_type} 
        Amount: {message.amount} {message.currency}
        Route: {message.sender_bic} → {message.receiver_bic}
        
        
        Perform initial triage assessment. Respond with JSON:
        {{
            "triage_decision": "GREEN|YELLOW|RED",
            "immediate_concerns": ["list of immediate red flags"],
            "requires_deep_analysis": true/false,
            "escalation_priority": "LOW|MEDIUM|HIGH|CRITICAL",
            "initial_reasoning": "Quick assessment reasoning",
            "focus_areas": ["areas that need deeper analysis"],
            "time_sensitivity": "How urgent is this review?"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "No response from screener", "triage_decision": "RED"}
            
        except Exception as e:
            return {"error": str(e), "triage_decision": "RED"}
    
    def _run_technical_analyst(self, message: SWIFTMessage, screener_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Deep technical validation and format analysis"""
        
        system_prompt = """You are a Technical SWIFT Analyst specializing in message format validation and technical compliance.
        You examine SWIFT messages for technical irregularities, format violations, and technical fraud indicators.
        You build upon the initial screener's assessment with detailed technical analysis."""
        
        user_prompt = f"""
        TECHNICAL ANALYSIS REQUEST
        
        TRANSACTION DETAILS:
        Message ID: {message.message_id}
        Type: {message.message_type}
        Reference: {message.reference}
        Amount: {message.amount} {message.currency}
        Sender BIC: {message.sender_bic}
        Receiver BIC: {message.receiver_bic}
        Value Date: {message.value_date}
        
        INITIAL SCREENER ASSESSMENT:
        Triage: {screener_result.get('triage_decision', 'UNKNOWN')}
        Priority: {screener_result.get('escalation_priority', 'UNKNOWN')}
        Focus Areas: {screener_result.get('focus_areas', [])}
        Initial Concerns: {screener_result.get('immediate_concerns', [])}
        
        Perform detailed technical analysis. Respond with JSON:
        {{
            "technical_validation": {{
                "format_compliance": "VALID|MINOR_ISSUES|MAJOR_ISSUES|INVALID",
                "bic_validation": "Analysis of BIC codes",
                "amount_analysis": "Analysis of amount patterns",
                "reference_check": "Reference number validation"
            }},
            "technical_concerns": ["specific technical red flags"],
            "data_integrity": "Assessment of data consistency",
            "agrees_with_screener": true/false,
            "technical_reasoning": "Detailed technical analysis",
            "recommend_next_step": "What should the risk assessor focus on?"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "No response from technical analyst"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _run_risk_assessor(self, message: SWIFTMessage, screener_result: Dict[str, Any], technical_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Risk pattern analysis and behavioral assessment"""
        
        system_prompt = """You are a Risk Assessment Specialist focused on behavioral patterns and risk profiling.
        You analyze transaction patterns, risk behaviors, and contextual factors that indicate potential fraud.
        You consider both the initial screening and technical analysis in your assessment."""
        
        user_prompt = f"""
        RISK PATTERN ANALYSIS
        
        TRANSACTION CONTEXT:
        Message: {message.message_id} ({message.message_type})
        Amount: {message.amount} {message.currency}  
        Banks: {message.sender_bic} → {message.receiver_bic}
        
        PREVIOUS ANALYSIS CHAIN:
        
        SCREENER SAYS: {screener_result.get('triage_decision', 'UNKNOWN')} priority
        - Concerns: {screener_result.get('immediate_concerns', [])}
        - Focus Areas: {screener_result.get('focus_areas', [])}
        
        TECHNICAL ANALYST SAYS: {technical_result.get('technical_validation', {}).get('format_compliance', 'UNKNOWN')}
        - Technical Concerns: {technical_result.get('technical_concerns', [])}
        - Data Integrity: {technical_result.get('data_integrity', 'Unknown')}
        - Agrees with Screener: {technical_result.get('agrees_with_screener', 'Unknown')}
        
        Now perform risk behavior analysis. Respond with JSON:
        {{
            "risk_assessment": {{
                "behavioral_score": 0.0-1.0,
                "pattern_analysis": "Analysis of suspicious patterns",
                "contextual_factors": ["relevant risk factors"],
                "historical_comparison": "How this compares to known patterns"
            }},
            "agent_consensus": "Do you agree with previous agents' assessments?",
            "risk_recommendation": "APPROVE|INVESTIGATE|BLOCK",
            "confidence_level": 0.0-1.0,
            "risk_reasoning": "Detailed risk assessment reasoning",
            "escalation_advice": "What should compliance focus on?"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "No response from risk assessor"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _run_compliance_officer(self, message: SWIFTMessage, chain_results: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Regulatory compliance and legal assessment"""
        
        system_prompt = """You are a Compliance Officer specializing in financial regulations and anti-money laundering.
        You review transactions for regulatory compliance, legal requirements, and policy violations.
        You consider all previous analysis in making compliance recommendations."""
        
        screener = chain_results.get("screener", {})
        technical = chain_results.get("technical_analyst", {})
        risk = chain_results.get("risk_assessor", {})
        
        user_prompt = f"""
        COMPLIANCE REVIEW
        
        TRANSACTION: {message.message_id}
        Amount: {message.amount} {message.currency}
        Route: {message.sender_bic} → {message.receiver_bic}
        
        AGENT CONSULTATION SUMMARY:
        
        SCREENER (Triage): {screener.get('triage_decision', 'UNKNOWN')}
        - Priority: {screener.get('escalation_priority', 'UNKNOWN')}
        - Immediate Concerns: {screener.get('immediate_concerns', [])}
        
        TECHNICAL ANALYST: {technical.get('technical_validation', {}).get('format_compliance', 'UNKNOWN')}
        - Technical Issues: {technical.get('technical_concerns', [])}
        - Recommends: {technical.get('recommend_next_step', 'Standard review')}
        
        RISK ASSESSOR: {risk.get('risk_recommendation', 'UNKNOWN')}
        - Risk Score: {risk.get('risk_assessment', {}).get('behavioral_score', 'Unknown')}
        - Pattern Concerns: {risk.get('risk_assessment', {}).get('contextual_factors', [])}
        
        Perform compliance assessment. Respond with JSON:
        {{
            "compliance_status": "COMPLIANT|QUESTIONABLE|NON_COMPLIANT|REQUIRES_INVESTIGATION",
            "regulatory_concerns": ["specific regulatory issues"],
            "aml_assessment": "Anti-money laundering evaluation",
            "policy_violations": ["any policy violations detected"],
            "legal_risk": "LOW|MEDIUM|HIGH|CRITICAL",
            "required_documentation": ["additional documentation needed"],
            "compliance_reasoning": "Detailed compliance analysis",
            "final_recommendation": "What action should be taken?"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "No response from compliance officer"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _run_final_reviewer(self, message: SWIFTMessage, chain_results: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Final synthesis and decision making"""
        
        system_prompt = """You are the Final Reviewing Authority for SWIFT transaction analysis.
        Your role is to synthesize all expert opinions, resolve conflicts, and make the final decision.
        You must provide clear reasoning and actionable recommendations."""
        
        screener = chain_results.get("screener", {})
        technical = chain_results.get("technical_analyst", {})
        risk = chain_results.get("risk_assessor", {})
        compliance = chain_results.get("compliance_officer", {})
        
        user_prompt = f"""
        FINAL REVIEW AND DECISION
        
        TRANSACTION: {message.message_id}
        Amount: {message.amount} {message.currency}
        
        EXPERT TEAM CONSULTATION RESULTS:
        
        🔍 INITIAL SCREENER:
        - Decision: {screener.get('triage_decision', 'UNKNOWN')}
        - Priority: {screener.get('escalation_priority', 'UNKNOWN')}
        - Concerns: {screener.get('immediate_concerns', [])}
        
        🔧 TECHNICAL ANALYST:
        - Validation: {technical.get('technical_validation', {}).get('format_compliance', 'UNKNOWN')}
        - Issues: {technical.get('technical_concerns', [])}
        - Agrees with Screener: {technical.get('agrees_with_screener', 'Unknown')}
        
        📊 RISK ASSESSOR:
        - Recommendation: {risk.get('risk_recommendation', 'UNKNOWN')}
        - Risk Score: {risk.get('risk_assessment', {}).get('behavioral_score', 'Unknown')}
        - Confidence: {risk.get('confidence_level', 'Unknown')}
        
        ⚖️ COMPLIANCE OFFICER:
        - Status: {compliance.get('compliance_status', 'UNKNOWN')}
        - Legal Risk: {compliance.get('legal_risk', 'UNKNOWN')}
        - Final Rec: {compliance.get('final_recommendation', 'Unknown')}
        
        SYNTHESIZE ALL EXPERT OPINIONS AND MAKE FINAL DECISION. Respond with JSON:
        
        {{
            "final_decision": "APPROVE|HOLD|REJECT",
            "confidence_score": 0.0-1.0,
            "risk_level": "LOW|MEDIUM|HIGH|CRITICAL", 
            "consensus_reasoning": "How you weighed all expert opinions",
            "conflict_resolution": "How you resolved any conflicting opinions",
            "recommended_actions": ["specific actions to take"],
            "business_impact": "Potential impact of this decision",
            "review_timeline": "When this should be reviewed again",
            "expert_agreement": "Level of agreement among experts",
            "decision_factors": ["key factors that influenced final decision"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "No response from final reviewer"}
            
        except Exception as e:
            return {"error": str(e)}
    