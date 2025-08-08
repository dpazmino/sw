"""
Demonstration of the Transaction Analyzer Class

This script shows how the Transaction Analyzer provides comprehensive
transaction analysis capabilities including balance validation, 
amount verification, and transaction integrity checks.
"""

from decimal import Decimal
from agents.transaction_analyzer import TransactionAnalyzer
from models.swift_message import SWIFTMessage
from utils.logger import setup_logger


def create_sample_swift_messages():
    """Create sample SWIFT messages for testing"""
    messages = [
        SWIFTMessage(
            message_type="MT103",
            reference="FT123456789",
            sender_bic="CHASUS33XXX",
            receiver_bic="DEUTDEFFXXX", 
            amount="1000000.00",
            currency="USD",
            value_date="250808",
            message_id="TXN001",
            ordering_customer="Global Corp Inc",
            beneficiary="European Trading Ltd",
            remittance_info="Q3 payment for services"
        ),
        SWIFTMessage(
            message_type="MT202",
            reference="FT987654321",
            sender_bic="BNPAFRPPXXX",
            receiver_bic="HSBCHKHXXXX",
            amount="500000.50",
            currency="EUR", 
            value_date="250808",
            message_id="TXN002",
            ordering_customer="French Bank SA",
            beneficiary="Hong Kong Trading Co",
            remittance_info="Interbank settlement"
        ),
        SWIFTMessage(
            message_type="MT103",
            reference="FT555444333",
            sender_bic="BOFAUS3NXXX",
            receiver_bic="RZBAATWWXXX",
            amount="250000.75",
            currency="USD",
            value_date="250808", 
            message_id="TXN003",
            ordering_customer="US Manufacturing LLC",
            beneficiary="Austrian Imports GmbH",
            remittance_info="Equipment purchase payment"
        )
    ]
    return messages


def demonstrate_transaction_analyzer():
    """Demonstrate Transaction Analyzer capabilities"""
    
    logger = setup_logger(__name__)
    print("🔧 Transaction Analyzer Class Demonstration")
    print("=" * 60)
    
    # Initialize the Transaction Analyzer
    analyzer = TransactionAnalyzer()
    print("✅ Transaction Analyzer initialized")
    
    # Create sample SWIFT messages
    swift_messages = create_sample_swift_messages()
    print(f"\n📧 Created {len(swift_messages)} sample SWIFT messages")
    
    print(f"\n🔄 Converting SWIFT messages to balanced transactions...")
    
    # Convert SWIFT messages to transactions
    transactions = []
    for message in swift_messages:
        try:
            transaction = analyzer.convert_swift_to_transaction(message)
            transactions.append(transaction)
            print(f"   ✅ {message.message_id}: ${float(message.amount):,.2f} {message.currency}")
        except Exception as e:
            print(f"   ❌ {message.message_id}: Failed - {str(e)}")
    
    print(f"\n⚖️ Validating transaction balances...")
    
    # Validate each transaction
    balanced_count = 0
    for transaction in transactions:
        validation = analyzer.validate_transaction_balance(transaction)
        
        if validation["is_balanced"]:
            balanced_count += 1
            print(f"   ✅ {transaction.original_message_id}: Balanced")
        else:
            print(f"   ⚠️ {transaction.original_message_id}: Unbalanced by ${validation['difference']:.2f}")
            
            # Try to fix the balance
            fixed_transaction = analyzer.fix_transaction_balance(transaction)
            revalidation = analyzer.validate_transaction_balance(fixed_transaction)
            
            if revalidation["is_balanced"]:
                print(f"      🔧 Fixed automatically!")
                balanced_count += 1
            else:
                print(f"      ❌ Could not fix balance")
    
    print(f"\n📊 Batch Validation Results:")
    batch_results = analyzer.batch_validate_transactions(transactions)
    print(f"   Total Transactions: {batch_results['total_transactions']}")
    print(f"   Balanced: {batch_results['balanced_transactions']}")
    print(f"   Unbalanced: {batch_results['unbalanced_transactions']}")
    print(f"   Total Difference: ${batch_results['total_difference']:.2f}")
    
    print(f"\n📈 Transaction Pattern Analysis:")
    pattern_analysis = analyzer.analyze_transaction_patterns(transactions)
    print(f"   Total Amount: ${pattern_analysis['total_amount']:,.2f}")
    print(f"   Average Amount: ${pattern_analysis['average_amount']:,.2f}")
    print(f"   Currency Breakdown: {pattern_analysis['currency_breakdown']}")
    print(f"   Split Patterns: {pattern_analysis['split_patterns']}")
    
    if pattern_analysis.get('anomalies'):
        print(f"   Anomalies Detected: {len(pattern_analysis['anomalies'])}")
        for anomaly in pattern_analysis['anomalies'][:3]:  # Show first 3
            print(f"      • {anomaly}")
    else:
        print(f"   No anomalies detected")
    
    print(f"\n🎯 Transaction Analyzer Benefits:")
    benefits = [
        "✅ Automatic balance validation and correction",
        "🔧 Precise decimal handling with proper rounding", 
        "📊 Comprehensive pattern analysis across transactions",
        "⚡ Batch processing capabilities for efficiency",
        "🛡️ Error handling and recovery mechanisms",
        "📈 Statistical analysis for anomaly detection"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print(f"\n🔗 Integration with Agent Patterns:")
    integrations = [
        "🤖 Prompt Chaining: Provides balanced data for AI analysis",
        "⚖️ Orchestrator-Worker: Fixes balance issues in transaction splits", 
        "🔄 Routing: Analyzes patterns for better fraud detection",
        "📊 Evaluator-Optimizer: Validates financial data integrity"
    ]
    
    for integration in integrations:
        print(f"   {integration}")
    
    print(f"\n" + "=" * 60)
    print("🎉 Transaction Analyzer Demonstration Complete!")
    print("   This class is now integrated into your SWIFT processing system")
    print("   and helps resolve the balance validation issues.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demonstrate_transaction_analyzer()
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("Check your environment setup and dependencies.")