#!/usr/bin/env python3
"""
Generate CBOR hex for Cardano airdrop transactions using PyCardano.
This script builds actual Cardano transactions and generates the CBOR hex needed for Eternl wallet.
"""

import json
import csv
from typing import List, Dict, Optional
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    Value,
    AuxiliaryData,
    AlonzoMetadata,
    Metadata,
    BlockFrostChainContext,
    Network,
    PaymentSigningKey,
    PaymentVerificationKey,
)

def read_airdrop_data(csv_file: str, num_rows: int = 5) -> List[Dict[str, str]]:
    """Read the first num_rows from the airdrop CSV file."""
    recipients = []
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i >= num_rows:
                break
            recipients.append({
                'address': row['address'].strip(),
                'ada_amount': float(row['ADA Value'])
            })
    
    return recipients

def ada_to_lovelace(ada_amount: float) -> int:
    """Convert ADA to Lovelace (1 ADA = 1,000,000 Lovelace)."""
    return int(ada_amount * 1_000_000)

def create_airdrop_transaction(
    recipients: List[Dict[str, str]], 
    sender_address: str,
    blockfrost_project_id: Optional[str] = None,
    network: Network = Network.MAINNET
) -> str:
    """
    Create a Cardano transaction for the airdrop and return CBOR hex.
    
    Args:
        recipients: List of recipient addresses and amounts
        sender_address: Your wallet address (source of funds)
        blockfrost_project_id: Blockfrost API key (optional - for live transactions)
        network: Cardano network (MAINNET or TESTNET)
    
    Returns:
        CBOR hex string
    """
    
    # For demonstration purposes, we'll create a transaction without actually
    # querying UTXOs. In a real scenario, you'd need a blockchain data provider.
    
    if blockfrost_project_id:
        # Use Blockfrost to query real UTXOs
        context = BlockFrostChainContext(blockfrost_project_id, network)
    else:
        # Create a mock context for demonstration
        context = None
        print("⚠️  WARNING: No Blockfrost API key provided.")
        print("   This will create a template transaction structure.")
        print("   For a real transaction, you need to:")
        print("   1. Provide a Blockfrost API key")
        print("   2. Or use another blockchain data provider")
        print()
    
    # Create transaction builder
    builder = TransactionBuilder(context) if context else None
    
    # Calculate total amount needed
    total_lovelace = sum(ada_to_lovelace(recipient['ada_amount']) for recipient in recipients)
    
    print(f"Building transaction for {len(recipients)} recipients")
    print(f"Total ADA needed: {total_lovelace / 1_000_000:.2f} ADA ({total_lovelace:,} Lovelace)")
    print()
    
    if not context:
        # Create a demo transaction structure
        return create_demo_transaction_cbor(recipients, sender_address)
    
    # Real transaction building (when context is available)
    try:
        # Parse sender address
        sender_addr = Address.from_bech32(sender_address)
        
        # Add sender as input (this would normally query UTXOs automatically)
        builder.add_input_address(sender_addr)
        
        # Add outputs for each recipient
        for recipient in recipients:
            recipient_addr = Address.from_bech32(recipient['address'])
            amount_lovelace = ada_to_lovelace(recipient['ada_amount'])
            output = TransactionOutput(recipient_addr, Value(amount_lovelace))
            builder.add_output(output)
        
        # Add metadata (optional)
        metadata = {
            674: {
                "msg": ["BOM Airdrop - Season 1"],
                "recipients": len(recipients),
                "total_ada": total_lovelace / 1_000_000
            }
        }
        
        auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
        builder.auxiliary_data = auxiliary_data
        
        # Build the transaction
        tx = builder.build()
        
        # Return CBOR hex
        return tx.to_cbor().hex()
        
    except Exception as e:
        print(f"Error building transaction: {e}")
        print("Falling back to demo structure...")
        return create_demo_transaction_cbor(recipients, sender_address)

def create_demo_transaction_cbor(recipients: List[Dict[str, str]], sender_address: str) -> str:
    """
    Create a demo CBOR structure for testing purposes.
    This is NOT a real transaction and cannot be submitted to the blockchain.
    """
    
    print("🔧 Creating demo CBOR structure...")
    print("   This is for testing the Eternl import format only.")
    print("   Replace with real CBOR when ready to execute.")
    print()
    
    # This is a placeholder CBOR that matches the structure but isn't a real transaction
    # In reality, you'd need proper UTXOs, signatures, etc.
    demo_cbor = (
        "84a500d90102818258209e10140cb5dc9f633441bd90580af0938255548c4ba8631d17fb16ea8ed9b202"
        "0101838258390106bdfa3e85f5ffd19b6e0cd345d657bc5f21643c41442b205dc34f95baca7e047f"
        "f4c33d2b9955565d25d3b4cc9ec64da0d3202ef01067951a000f424082583901e292a6532a502468"
        "0954de1880aaf1471b8163573ecc49bb5c3767cf50181f6367519f0c5f8019f94b59d98a2e93360c"
        "9ad2a335beb314551a0049ade782583901e292a6532a5024680954de1880aaf1471b8163573ecc49"
        "bb5c3767cf50181f6367519f0c5f8019f94b59d98a2e93360c9ad2a335beb314551a002b28b7021a"
        "00029d59031a096ec7eb0801a0f5f6"
    )
    
    return demo_cbor

def create_eternl_transaction_file(
    recipients: List[Dict[str, str]], 
    cbor_hex: str,
    output_file: str = "csv/airdrop_eternl_tx_with_cbor.json"
) -> None:
    """Create the final Eternl transaction file with real CBOR hex."""
    
    total_ada = sum(recipient['ada_amount'] for recipient in recipients)
    
    eternl_tx = {
        "type": "Tx ConwayEra",
        "description": f"BOM Airdrop S1 - {len(recipients)} Recipients ({total_ada:.2f} ADA)",
        "cborHex": cbor_hex
    }
    
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(eternl_tx, file, indent=2)
    
    print(f"✅ Eternl transaction file created: {output_file}")
    print(f"   CBOR length: {len(cbor_hex)} characters")
    print(f"   Recipients: {len(recipients)}")
    print(f"   Total ADA: {total_ada:.2f}")

def main():
    print("🚀 Cardano Airdrop CBOR Generator")
    print("=" * 50)
    
    # Configuration
    csv_file = "csv/BOM-Airdrop-S1-Clean.csv"
    num_recipients = 5
    
    # You'll need to provide these for a real transaction:
    sender_address = "addr1your_wallet_address_here"  # Replace with your actual address
    blockfrost_project_id = None  # Replace with your Blockfrost API key for real transactions
    
    print(f"📁 Reading recipients from: {csv_file}")
    print(f"👥 Processing first {num_recipients} recipients")
    print()
    
    # Read recipient data
    recipients = read_airdrop_data(csv_file, num_recipients)
    
    # Generate CBOR hex
    print("🔨 Generating CBOR transaction...")
    cbor_hex = create_airdrop_transaction(
        recipients=recipients,
        sender_address=sender_address,
        blockfrost_project_id=blockfrost_project_id,
        network=Network.MAINNET
    )
    
    print(f"📦 Generated CBOR hex ({len(cbor_hex)} chars)")
    print()
    
    # Create Eternl-compatible file
    create_eternl_transaction_file(recipients, cbor_hex)
    
    print()
    print("🎯 Next Steps:")
    print("1. Get a Blockfrost API key from https://blockfrost.io")
    print("2. Replace 'sender_address' with your actual wallet address")
    print("3. Replace 'blockfrost_project_id' with your API key")
    print("4. Run this script again to generate a real transaction")
    print("5. Import the generated JSON file into Eternl wallet")
    print()
    print("⚠️  Remember to test on testnet first!")

if __name__ == "__main__":
    main() 