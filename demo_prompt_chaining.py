"""
Demonstration of Prompt Chaining Pattern in SWIFT Transaction Processing

This script shows how the prompt chaining agent works by analyzing a single
SWIFT transaction through a conversation between 5 specialized AI agents.
"""

import logging
from models.swift_message import SWIFTMessage
from agents.prompt_chaining import PromptChainingAgent
from config import Config
from utils.logger import setup_logger


def create_sample_transaction() -> SWIFTMessage:
    """Create a sample SWIFT transaction for demonstration"""
    return SWIFTMessage(
        message_id="PC-DEMO-001",
        message_type="MT103",
        reference="FT12345678",
        sender_bic="DEUTDEFF",  # Deutsche Bank
        receiver_bic="CHASUS33",  # JPMorgan Chase
        amount="2500000.00",  # High amount - will trigger scrutiny
        currency="USD",
        value_date="2024-08-08",
        ordering_customer="ACME Corporation Ltd",
        beneficiary="Global Trading Partners Inc",
        remittance_info="Invoice payment for Q3 2024"
    )


def main():
    """Demonstrate prompt chaining analysis"""
    
    # Set up logging
    logger = setup_logger(__name__)
    logger.info("Starting Prompt Chaining Demonstration")
    
    try:
        # Initialize the prompt chaining agent
        chaining_agent = PromptChainingAgent()
        
        # Create a sample transaction
        sample_transaction = create_sample_transaction()
        
        # Simulated fraud detection inputs
        initial_fraud_score = 0.65  # High risk score
        fraud_indicators = [
            "High amount transaction",
            "Weekend processing",
            "Cross-border transfer", 
            "New beneficiary relationship"
        ]
        
        logger.info(f"Analyzing transaction {sample_transaction.message_id}")
        logger.info(f"Amount: {sample_transaction.amount} {sample_transaction.currency}")
        logger.info(f"Route: {sample_transaction.sender_bic} → {sample_transaction.receiver_bic}")
        logger.info(f"Initial fraud score: {initial_fraud_score}")
        logger.info(f"Risk indicators: {', '.join(fraud_indicators)}")
        
        print("\n" + "="*80)
        print("🔗 PROMPT CHAINING ANALYSIS DEMONSTRATION")
        print("="*80)
        
        print(f"\n📋 TRANSACTION DETAILS:")
        print(f"   ID: {sample_transaction.message_id}")
        print(f"   Type: {sample_transaction.message_type}")
        print(f"   Amount: ${float(sample_transaction.amount):,.2f} {sample_transaction.currency}")
        print(f"   Route: {sample_transaction.sender_bic} → {sample_transaction.receiver_bic}")
        print(f"   Fraud Score: {initial_fraud_score:.2f}")
        print(f"   Risk Flags: {', '.join(fraud_indicators)}")
        
        print(f"\n🤖 STARTING AI AGENT CONSULTATION CHAIN...")
        
        # Run the prompt chain analysis
        result = chaining_agent.analyze_transaction_chain(
            sample_transaction, 
            initial_fraud_score, 
            fraud_indicators
        )
        
        # Display results
        print(f"\n✅ CHAIN ANALYSIS COMPLETE!")
        print(f"   Processing Time: {result['chain_metadata']['total_processing_time']:.2f}s")
        print(f"   Steps Completed: {result['chain_metadata']['steps_completed']}")
        
        # Show final decision
        final_analysis = result['chain_analysis']
        print(f"\n🎯 FINAL DECISION:")
        print(f"   Decision: {final_analysis['final_decision']}")
        print(f"   Confidence: {final_analysis.get('confidence_score', 0):.2f}")
        print(f"   Risk Level: {final_analysis.get('risk_level', 'UNKNOWN')}")
        
        if final_analysis.get('recommended_actions'):
            print(f"\n📝 RECOMMENDED ACTIONS:")
            for action in final_analysis['recommended_actions']:
                print(f"   • {action}")
        
        # Show agent perspectives
        print(f"\n🧠 AGENT PERSPECTIVES:")
        agent_perspectives = result.get('agent_perspectives', {})
        
        for agent_name, perspective in agent_perspectives.items():
            print(f"\n   {agent_name.upper().replace('_', ' ')}:")
            
            if agent_name == "screener":
                triage = perspective.get('triage_decision', 'UNKNOWN')
                priority = perspective.get('escalation_priority', 'UNKNOWN')
                print(f"      Triage: {triage} ({priority} priority)")
                
            elif agent_name == "technical_analyst":
                validation = perspective.get('technical_validation', {})
                compliance = validation.get('format_compliance', 'UNKNOWN')
                print(f"      Format Compliance: {compliance}")
                
            elif agent_name == "risk_assessor":
                recommendation = perspective.get('risk_recommendation', 'UNKNOWN')
                confidence = perspective.get('confidence_level', 'Unknown')
                print(f"      Recommendation: {recommendation} (Confidence: {confidence})")
                
            elif agent_name == "compliance_officer":
                status = perspective.get('compliance_status', 'UNKNOWN')
                legal_risk = perspective.get('legal_risk', 'UNKNOWN')
                print(f"      Compliance: {status} (Legal Risk: {legal_risk})")
                
            elif agent_name == "final_reviewer":
                reasoning = perspective.get('consensus_reasoning', 'No reasoning provided')[:100] + "..."
                print(f"      Reasoning: {reasoning}")
        
        print(f"\n" + "="*80)
        print("🎉 PROMPT CHAINING DEMONSTRATION COMPLETE!")
        print("="*80)
        
        logger.info("Prompt chaining demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR: {str(e)}")
        print("This might be due to missing OpenAI API key or connectivity issues.")


if __name__ == "__main__":
    main()