"""
Demonstration of Prompt Chaining Pattern in SWIFT Transaction Processing

This script shows how prompt chaining creates a conversation between specialized AI agents
for enhanced fraud analysis of SWIFT transactions.
"""

import json
from datetime import datetime
from typing import List

from agents.prompt_chaining import PromptChainingAgent
from models.swift_message import SWIFTMessage
from config import Config


def create_sample_swift_message() -> SWIFTMessage:
    """Create a sample SWIFT message for demonstration"""
    return SWIFTMessage(
        message_type="MT103",
        reference="FT21218ABC001",
        sender_bic="CHASUS33XXX",  # Chase Bank USA
        receiver_bic="DEUTDEFFXXX",  # Deutsche Bank Germany
        amount="500000.00",
        currency="USD",
        value_date="2025-08-08",
        message_id="DEMO001",
        ordering_customer="Acme Corp Trading Division",
        beneficiary="European Manufacturing Ltd",
        remittance_info="Payment for Q3 manufacturing contract"
    )


def demonstrate_prompt_chaining():
    """
    Demonstrate the prompt chaining pattern with a sample transaction
    """
    print("🔗 SWIFT Prompt Chaining Agent Demonstration")
    print("=" * 60)
    
    # Initialize the prompt chaining agent
    try:
        chain_agent = PromptChainingAgent()
        print("✅ Prompt Chaining Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        return
    
    # Create sample transaction
    sample_message = create_sample_swift_message()
    print(f"\n📧 Sample Transaction: {sample_message.message_id}")
    print(f"   Type: {sample_message.message_type}")
    print(f"   Amount: {sample_message.amount} {sample_message.currency}")
    print(f"   Route: {sample_message.sender_bic} → {sample_message.receiver_bic}")
    
    # Simulate fraud detection inputs
    fraud_score = 0.65  # Medium-high risk
    fraud_indicators = [
        "High amount transaction",
        "Cross-border payment",
        "Weekend processing",
        "First-time beneficiary"
    ]
    
    print(f"\n🚨 Fraud Detection Inputs:")
    print(f"   Fraud Score: {fraud_score:.2f}")
    print(f"   Risk Indicators: {', '.join(fraud_indicators)}")
    
    print(f"\n🔗 Starting Prompt Chain Analysis...")
    print("   Creating conversation between specialized AI agents:")
    print("   1. Initial Screener → 2. Technical Analyst → 3. Risk Assessor")
    print("   4. Compliance Officer → 5. Final Reviewer")
    
    # Run prompt chain analysis
    try:
        start_time = datetime.now()
        
        result = chain_agent.analyze_transaction_chain(
            sample_message,
            fraud_score,
            fraud_indicators
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Prompt Chain Analysis Completed in {processing_time:.2f} seconds")
        
        # Display results
        display_chain_results(result)
        
    except Exception as e:
        print(f"❌ Prompt chain analysis failed: {str(e)}")


def display_chain_results(result: dict):
    """Display the results of prompt chain analysis"""
    
    print("\n" + "=" * 60)
    print("📊 PROMPT CHAIN ANALYSIS RESULTS")
    print("=" * 60)
    
    # Final Decision
    chain_analysis = result.get("chain_analysis", {})
    print(f"\n🎯 FINAL DECISION: {chain_analysis.get('final_decision', 'UNKNOWN')}")
    print(f"   Confidence Score: {chain_analysis.get('confidence_score', 0):.2f}")
    print(f"   Risk Level: {chain_analysis.get('risk_level', 'UNKNOWN')}")
    
    # Consensus Reasoning
    reasoning = chain_analysis.get('consensus_reasoning', 'No reasoning provided')
    print(f"\n💭 CONSENSUS REASONING:")
    print(f"   {reasoning}")
    
    # Recommended Actions
    actions = chain_analysis.get('recommended_actions', [])
    if actions:
        print(f"\n📝 RECOMMENDED ACTIONS:")
        for i, action in enumerate(actions, 1):
            print(f"   {i}. {action}")
    
    # Agent Perspectives
    perspectives = result.get("agent_perspectives", {})
    print(f"\n👥 AGENT PERSPECTIVES:")
    
    for agent_name, agent_result in perspectives.items():
        print(f"\n   🔸 {agent_name.upper()}")
        
        # Extract key insights from each agent
        if "triage_decision" in agent_result:
            print(f"      Decision: {agent_result.get('triage_decision', 'N/A')}")
            print(f"      Priority: {agent_result.get('escalation_priority', 'N/A')}")
        
        if "technical_validation" in agent_result:
            compliance = agent_result.get('technical_validation', {}).get('format_compliance', 'N/A')
            print(f"      Format Compliance: {compliance}")
        
        if "risk_recommendation" in agent_result:
            print(f"      Risk Recommendation: {agent_result.get('risk_recommendation', 'N/A')}")
            print(f"      Confidence: {agent_result.get('confidence_level', 'N/A')}")
        
        if "compliance_status" in agent_result:
            print(f"      Compliance Status: {agent_result.get('compliance_status', 'N/A')}")
            print(f"      Legal Risk: {agent_result.get('legal_risk', 'N/A')}")
        
        if "final_decision" in agent_result:
            print(f"      Final Decision: {agent_result.get('final_decision', 'N/A')}")
            factors = agent_result.get('decision_factors', [])
            if factors:
                print(f"      Key Factors: {', '.join(factors[:3])}")  # Show first 3 factors
    
    # Chain Metadata
    metadata = result.get("chain_metadata", {})
    print(f"\n📈 CHAIN METADATA:")
    print(f"   Processing Time: {metadata.get('total_processing_time', 0):.2f} seconds")
    print(f"   Steps Completed: {metadata.get('steps_completed', 0)}")
    print(f"   Analysis Timestamp: {metadata.get('analysis_timestamp', 'N/A')}")
    
    print("\n" + "=" * 60)


def demonstrate_pattern_benefits():
    """Explain the benefits of prompt chaining pattern"""
    
    print("\n🌟 PROMPT CHAINING PATTERN BENEFITS")
    print("=" * 60)
    
    benefits = [
        "🎯 **Specialized Expertise**: Each AI agent has a specific role and expertise",
        "🔄 **Contextual Conversation**: Agents build on previous analysis for deeper insights",
        "⚖️ **Conflict Resolution**: Final reviewer synthesizes conflicting opinions",
        "📊 **Comprehensive Analysis**: Multiple perspectives ensure thorough evaluation",
        "🔍 **Transparency**: Clear reasoning chain shows how decisions were made",
        "⚡ **Scalability**: Can process multiple transactions with consistent quality",
        "🛡️ **Reduced Bias**: Multiple agents help identify and mitigate individual biases"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print("\n🔗 **How It Works in Your SWIFT System:**")
    print("   1. **Initial Screener** quickly triages transactions")
    print("   2. **Technical Analyst** performs deep format validation")
    print("   3. **Risk Assessor** analyzes behavioral patterns")
    print("   4. **Compliance Officer** checks regulatory requirements")
    print("   5. **Final Reviewer** synthesizes all findings into decision")
    
    print("\n✨ **Integration with Other Patterns:**")
    print("   - Enhances **Routing Pattern** with smarter decision-making")
    print("   - Complements **Evaluator-Optimizer** with multi-perspective validation")
    print("   - Feeds better data into **Orchestrator-Worker** for final processing")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        demonstrate_prompt_chaining()
        demonstrate_pattern_benefits()
        
        print("\n🎉 Prompt Chaining Demo Completed Successfully!")
        print("    This pattern is now integrated into your SWIFT processing system.")
        print("    High-risk transactions will receive enhanced multi-agent analysis.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("    Check your OpenAI API key configuration.")