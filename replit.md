# Overview

This is a SWIFT (Society for Worldwide Interbank Financial Telecommunication) transaction processing system that implements multiple agent patterns for financial message validation, fraud detection, and transaction processing. The system generates synthetic SWIFT messages across multiple banks, validates them against international standards, detects potential fraud using statistical methods like Benford's Law, and processes transactions with splitting capabilities.

The application demonstrates enterprise-level financial processing patterns including concurrent message handling, LLM-powered fraud analysis, and comprehensive validation workflows typical of international banking systems.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Agent Patterns
The system implements five distinct agent patterns for distributed processing:

1. **Evaluator-Optimizer Pattern** - Validates SWIFT messages against international standards and attempts automatic corrections using iterative refinement
2. **Parallelization Pattern** - Processes multiple messages concurrently using thread pools with configurable batch sizes and worker counts
3. **Routing Pattern** - Routes messages based on fraud detection scores using Benford's Law statistical analysis and risk indicators
4. **Prompt Chaining Pattern** - Creates conversations between specialized AI agents (Screener, Technical Analyst, Risk Assessor, Compliance Officer, Final Reviewer) for enhanced fraud analysis through multi-step reasoning
5. **Orchestrator-Worker Pattern** - Coordinates transaction splitting across multiple worker threads for parallel processing

## Data Models
The system uses Pydantic models for strict data validation:
- **SWIFTMessage** - Core financial message with MT103/MT202 support, BIC validation, and processing status tracking
- **Bank** - Financial institution data with BIC codes, risk scoring, and geographic information
- **Transaction/TransactionSplit** - Transaction processing models supporting company fees and multi-split accounting
- **ValidationResult** - Structured validation outcomes with errors and warnings

## Processing Pipeline
Messages flow through a multi-stage pipeline:
1. **Generation** - Creates realistic synthetic SWIFT messages using Faker library
2. **Validation** - Multi-iteration validation with automatic correction attempts
3. **Fraud Detection** - Statistical analysis using Benford's Law and pattern matching
4. **Routing** - Directs messages to appropriate processing queues based on risk scores
5. **Prompt Chaining Analysis** - High-risk transactions undergo detailed analysis through AI agent conversations for enhanced decision-making
6. **Transaction Processing** - Splits transactions into company fees and account components

## Fraud Detection System
Implements comprehensive fraud detection using:
- **Benford's Law Analysis** - Statistical detection of suspicious first-digit distributions
- **Pattern Recognition** - Rule-based detection of high-risk transaction patterns
- **LLM Review** - OpenAI GPT-4o integration for complex fraud analysis and decision making
- **Risk Scoring** - Multi-factor risk assessment with configurable thresholds

## Data Storage
Uses CSV-based data persistence for:
- Banks registry with BIC codes and risk profiles
- Transaction history and processing logs
- Fraud review records and decisions
- Processed transaction splits and accounting entries

## Configuration Management
Centralized configuration system supporting:
- Processing parameters (worker counts, batch sizes, thresholds)
- SWIFT validation rules and message type support
- OpenAI API integration settings
- Fraud detection sensitivity controls

# External Dependencies

## OpenAI Integration
- **Service**: OpenAI GPT-4o API
- **Purpose**: Advanced fraud analysis and transaction review
- **Configuration**: API key via environment variables
- **Usage**: Complex fraud pattern analysis and natural language decision making

## Python Libraries
- **Pydantic**: Data validation and serialization with strict typing
- **Faker**: Synthetic data generation for realistic SWIFT messages and bank information
- **NumPy/SciPy**: Statistical analysis for Benford's Law fraud detection
- **Pandas**: CSV data manipulation and analysis
- **ThreadPoolExecutor**: Concurrent processing for parallel agent patterns

## Data Format Dependencies
- **CSV Files**: Primary data storage for banks, transactions, and processing logs
- **JSON**: API communication format for OpenAI integration
- **ISO Standards**: SWIFT message formatting, BIC codes, and currency codes

## Financial Standards
- **SWIFT MT103/MT202**: International wire transfer message formats
- **ISO 9362**: BIC (Bank Identifier Code) validation standards
- **ISO 4217**: Currency code validation
- **Benford's Law**: Mathematical framework for fraud detection