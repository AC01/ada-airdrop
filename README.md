# Airdrop Automater

This repository contains two distinct but related projects for managing Cardano-based staking rewards and airdrops.

## Project Structure

### 📊 [Staking Results Processor](./staking-results-processor/)
Processes staking data for different seasons and generates comprehensive results CSV files.

**Key Features:**
- Season-agnostic staking data processing
- Promise completion tracking and statistics
- Combo bonuses, Seer rewards, and Heroes rewards calculation
- Comprehensive user ranking and performance analysis
- ADA value distribution calculations

**Main Files:**
- `season_2_processor.py` - Core processing engine
- `data/` - All staking-related CSV data files
- Generated results and comparison reports

### 🚀 [Airdrop Transaction Builder](./airdrop-transaction-builder/)
Builds Cardano transactions for airdrops using PyCardano with wallet compatibility.

**Key Features:**
- CBOR transaction building for Cardano
- Eternl wallet compatibility
- Multi-recipient airdrop support
- UTXO management and fee calculation
- Transaction verification and validation

**Main Files:**
- Multiple transaction builder scripts
- `run_with_your_details.py` - Configuration and execution
- `data/` - Airdrop recipient data and transaction files

## Workflow

1. **Process Staking Results** → Use the staking results processor to analyze user performance and calculate rewards
2. **Generate Airdrop Data** → Export qualified recipients and reward amounts
3. **Build Transactions** → Use the transaction builder to create airdrop transactions
4. **Execute Airdrop** → Sign and submit transactions through compatible wallets

## Getting Started

### Prerequisites
- Python 3.8+
- PyCardano library
- Pandas for data processing
- Access to Cardano node (for transaction building)

### Quick Start

1. **Process staking data:**
   ```bash
   cd staking-results-processor
   python season_2_processor.py
   ```

2. **Build airdrop transactions:**
   ```bash
   cd airdrop-transaction-builder
   python run_with_your_details.py
   ```

## Data Flow

```
Staking Data → Results Processor → Qualified Recipients → Transaction Builder → Signed Transactions → Airdrop Execution
```

## Important Notes

- Each project is self-contained with its own data directory
- Always test transactions with small amounts first
- Verify all recipient addresses before executing airdrops
- Review wallet compatibility documentation before proceeding

## Support

Each project directory contains detailed README files with specific usage instructions and troubleshooting information. 