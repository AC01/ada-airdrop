#!/usr/bin/env python3
"""
Generate REAL CBOR hex for Cardano airdrop transactions.
This script requires your wallet address and optionally a Blockfrost API key for real transactions.
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
)

def configure_transaction():
    """Interactive configuration for transaction parameters."""
    print("🔧 Transaction Configuration")
    print("=" * 40)
    
    # Get sender address
    sender_address = input("Enter your wallet address (addr1...): ").strip()
    if not sender_address.startswith('addr1'):
        print("⚠️  Warning: Address should start with 'addr1'")
    
    # Get Blockfrost API key (optional)
    print("\n📡 Blockchain Data Provider:")
    print("1. Blockfrost (recommended) - Get free API key at https://blockfrost.io")
    print("2. Skip (demo mode) - Will create template CBOR")
    
    choice = input("Choose option (1/2): ").strip()
    
    if choice == "1":
        api_key = input("Enter your Blockfrost project ID: ").strip()
        if not api_key:
            print("⚠️  No API key provided, using demo mode")
            api_key = None
    else:
        api_key = None
        print("📝 Using demo mode")
    
    # Network selection
    print("\n🌐 Network Selection:")
    print("1. Mainnet (real ADA)")
    print("2. Testnet (test ADA)")
    
    network_choice = input("Choose network (1/2): ").strip()
    network = Network.MAINNET if network_choice == "1" else Network.TESTNET
    
    # Number of recipients
    print("\n👥 Recipients:")
    num_recipients = int(input("How many recipients to process? (default: 5): ") or "5")
    
    return sender_address, api_key, network, num_recipients

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

def build_real_transaction(
    recipients: List[Dict[str, str]], 
    sender_address: str,
    blockfrost_project_id: str,
    network: Network
) -> str:
    """Build a real Cardano transaction with proper UTXOs."""
    
    try:
        # Create blockchain context
        context = BlockFrostChainContext(blockfrost_project_id, network)
        
        # Create transaction builder
        builder = TransactionBuilder(context)
        
        # Parse sender address
        sender_addr = Address.from_bech32(sender_address)
        
        # Add input from sender (this will automatically query and select UTXOs)
        builder.add_input_address(sender_addr)
        
        print(f"📡 Querying UTXOs for address: {sender_address[:20]}...")
        
        # Add outputs for each recipient
        total_lovelace = 0
        for recipient in recipients:
            recipient_addr = Address.from_bech32(recipient['address'])
            amount_lovelace = ada_to_lovelace(recipient['ada_amount'])
            total_lovelace += amount_lovelace
            
            output = TransactionOutput(recipient_addr, Value(amount_lovelace))
            builder.add_output(output)
            
            print(f"  → {recipient['address'][:20]}...{recipient['address'][-10:]} : {recipient['ada_amount']:.2f} ADA")
        
        print(f"\n💰 Total sending: {total_lovelace / 1_000_000:.2f} ADA")
        
        # Add metadata
        metadata = {
            674: {
                "msg": ["BOM Airdrop - Season 1"],
                "recipients": len(recipients),
                "total_ada": total_lovelace / 1_000_000,
                "created_by": "PyCardano Airdrop Script"
            }
        }
        
        auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
        builder.auxiliary_data = auxiliary_data
        
        # Build transaction
        print("🔨 Building transaction...")
        tx = builder.build()
        
        print("✅ Transaction built successfully!")
        print(f"   Transaction ID: {tx.id}")
        print(f"   Fee: {tx.transaction_body.fee / 1_000_000:.6f} ADA")
        
        # Return CBOR hex
        cbor_hex = tx.to_cbor().hex()
        print(f"   CBOR length: {len(cbor_hex)} characters")
        
        return cbor_hex
        
    except Exception as e:
        print(f"❌ Error building real transaction: {e}")
        print("💡 This might be due to:")
        print("   - Insufficient funds in wallet")
        print("   - Invalid Blockfrost API key")
        print("   - Network issues")
        print("   - Wallet has no UTXOs")
        raise

def build_demo_transaction(recipients: List[Dict[str, str]]) -> str:
    """Build a demo transaction for testing."""
    
    print("🔧 Building demo transaction...")
    print("   This CBOR is for testing Eternl import only")
    print("   It cannot be submitted to the blockchain")
    
    # Create a more realistic demo CBOR based on the recipients
    # This is still a template but matches the expected structure better
    demo_cbor = (
        "84a700d90102818258209e10140cb5dc9f633441bd90580af0938255548c4ba8631d17fb16ea8ed9b202"
        "01018782583901" +  # Start of outputs
        "".join([
            recipient['address'][4:] + hex(ada_to_lovelace(recipient['ada_amount']))[2:].zfill(16)
            for recipient in recipients[:3]  # Include first 3 recipients in demo
        ]) +
        "021a002dc6c0031a096ec7eb0758203d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
        "074d901029f4443424f4d416972647260ff0801a0f5f6"
    )
    
    return demo_cbor

def save_eternl_transaction(recipients: List[Dict[str, str]], cbor_hex: str, is_real: bool = False):
    """Save the transaction in Eternl format."""
    
    total_ada = sum(recipient['ada_amount'] for recipient in recipients)
    
    # Choose filename based on transaction type
    if is_real:
        filename = "csv/airdrop_REAL_eternl_tx.json"
        description = f"🚀 REAL BOM Airdrop S1 - {len(recipients)} Recipients ({total_ada:.2f} ADA)"
    else:
        filename = "csv/airdrop_DEMO_eternl_tx.json"
        description = f"🧪 DEMO BOM Airdrop S1 - {len(recipients)} Recipients ({total_ada:.2f} ADA)"
    
    eternl_tx = {
        "type": "Tx ConwayEra",
        "description": description,
        "cborHex": cbor_hex
    }
    
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(eternl_tx, file, indent=2)
    
    print(f"💾 Saved transaction: {filename}")
    return filename

def main():
    print("🎯 Real CBOR Generator for Cardano Airdrops")
    print("=" * 50)
    
    # Interactive configuration
    sender_address, blockfrost_api_key, network, num_recipients = configure_transaction()
    
    print(f"\n📋 Configuration Summary:")
    print(f"   Sender: {sender_address[:20]}...{sender_address[-10:]}")
    print(f"   Network: {network.name}")
    print(f"   Recipients: {num_recipients}")
    print(f"   API Key: {'✅ Provided' if blockfrost_api_key else '❌ Demo mode'}")
    print()
    
    # Read recipients
    csv_file = "csv/BOM-Airdrop-S1-Clean.csv"
    recipients = read_airdrop_data(csv_file, num_recipients)
    
    # Build transaction
    try:
        if blockfrost_api_key:
            # Build real transaction
            print("🚀 Building REAL transaction...")
            cbor_hex = build_real_transaction(recipients, sender_address, blockfrost_api_key, network)
            is_real = True
        else:
            # Build demo transaction
            cbor_hex = build_demo_transaction(recipients)
            is_real = False
        
        # Save Eternl transaction file
        filename = save_eternl_transaction(recipients, cbor_hex, is_real)
        
        print(f"\n🎉 Success!")
        print(f"📁 Transaction file: {filename}")
        
        if is_real:
            print(f"🔥 This is a REAL transaction ready for Eternl!")
            print(f"⚠️  Double-check recipients before importing to Eternl")
        else:
            print(f"🧪 This is a demo transaction for testing")
            print(f"💡 Run again with Blockfrost API for real transaction")
        
        print(f"\n📱 Next steps:")
        print(f"1. Open Eternl wallet")
        print(f"2. Go to 'Import Transaction'")
        print(f"3. Select the generated JSON file")
        print(f"4. Review transaction details")
        print(f"5. Sign and submit")
        
    except Exception as e:
        print(f"\n❌ Failed to build transaction: {e}")
        print("💡 Try demo mode first to test the workflow")

if __name__ == "__main__":
    main() 