# Airdrop Transaction Builder

This project builds Cardano transactions for airdrops using PyCardano and generates transaction files compatible with various Cardano wallets, particularly Eternl.

## Features

- Builds proper CBOR transactions for Cardano airdrops
- Generates wallet-compatible transaction files
- Handles UTXO management and transaction signing
- Supports multiple output addresses
- Compatible with Eternl wallet format
- Comprehensive transaction verification

## Files

### Core Transaction Builders
- `final_clean_transaction.py` - Final clean transaction builder
- `pycardano_real_cbor.py` - PyCardano CBOR transaction builder
- `build_proper_cbor.py` - Proper CBOR transaction builder
- `generate_real_cbor.py` - Real CBOR generator
- `generate_real_utxo_tx.py` - Real UTXO transaction generator
- `generate_cbor_tx.py` - CBOR transaction generator
- `build_airdrop_tx.py` - Main airdrop transaction builder

### Utilities
- `run_with_your_details.py` - Configuration and execution script
- `ETERNL_ISSUE_EXPLAINED.md` - Documentation about Eternl wallet compatibility issues

## Data Files

- `airdrop_*.json` - Various airdrop transaction files and metadata
- `eternl-*.json` - Eternl wallet specific transaction files
- `BOM-Airdrop-S1-Clean.csv` - Clean airdrop recipient data

## Usage

1. **Configure your details** in `run_with_your_details.py`
2. **Prepare recipient data** in the appropriate CSV format
3. **Run the transaction builder**:

```python
python run_with_your_details.py
```

## Transaction Flow

1. Load recipient data from CSV
2. Calculate transaction outputs and fees
3. Build CBOR transaction using PyCardano
4. Generate wallet-compatible transaction files
5. Output unsigned transaction for wallet signing

## Wallet Compatibility

The transaction builder generates files compatible with:
- Eternl Wallet (primary target)
- Other Cardano wallets supporting standard transaction formats

## Important Notes

- Always verify transaction details before signing
- Test with small amounts first
- Ensure sufficient UTXOs for transaction fees
- Review `ETERNL_ISSUE_EXPLAINED.md` for wallet-specific considerations

## File Outputs

- Unsigned transaction CBOR
- Wallet-specific JSON files
- Transaction metadata
- Verification data 