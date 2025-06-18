#!/usr/bin/env python3
"""
Generate CBOR transactions with REAL UTXOs for Eternl wallet.
This queries actual UTXOs from your wallet to create a signable transaction.
"""

import json
import csv
import requests
from typing import List, Dict, Optional
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    TransactionInput,
    TransactionBody,
    TransactionWitnessSet,
    Transaction,
    Value,
    AuxiliaryData,
    AlonzoMetadata,
    Metadata,
    Network,
    UTxO,
    BlockFrostChainContext,
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

def query_utxos_blockfrost(address: str, api_key: str, network: str = "mainnet") -> List[Dict]:
    """Query UTXOs from Blockfrost API."""
    
    base_url = f"https://cardano-{network}.blockfrost.io/api/v0"
    headers = {"project_id": api_key}
    
    try:
        response = requests.get(f"{base_url}/addresses/{address}/utxos", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error querying UTXOs: {e}")
        return []

def create_transaction_with_real_utxos(
    recipients: List[Dict[str, str]], 
    sender_address: str,
    blockfrost_api_key: Optional[str] = None
) -> str:
    """Create transaction with real UTXOs or provide instructions."""
    
    print(f"🔨 Creating transaction with REAL UTXOs")
    print(f"👤 Sender: {sender_address[:30]}...{sender_address[-15:]}")
    
    # Calculate total needed
    total_lovelace = sum(ada_to_lovelace(recipient['ada_amount']) for recipient in recipients)
    fee_estimate = 200_000  # 0.2 ADA
    total_needed = total_lovelace + fee_estimate
    
    print(f"💰 Total needed: {total_needed / 1_000_000:.2f} ADA")
    
    if blockfrost_api_key:
        print(f"📡 Querying real UTXOs from Blockfrost...")
        utxos_data = query_utxos_blockfrost(sender_address, blockfrost_api_key)
        
        if not utxos_data:
            print(f"❌ No UTXOs found or API error")
            return create_manual_utxo_instructions(recipients, sender_address, total_needed)
        
        print(f"✅ Found {len(utxos_data)} UTXOs")
        
        # Select UTXOs with enough ADA
        selected_utxos = []
        total_available = 0
        
        for utxo in utxos_data:
            ada_amount = int(utxo['amount'][0]['quantity'])  # Lovelace amount
            total_available += ada_amount
            selected_utxos.append(utxo)
            
            if total_available >= total_needed:
                break
        
        if total_available < total_needed:
            print(f"❌ Insufficient funds: {total_available / 1_000_000:.2f} ADA available, {total_needed / 1_000_000:.2f} ADA needed")
            return create_manual_utxo_instructions(recipients, sender_address, total_needed)
        
        # Build transaction with real UTXOs
        return build_transaction_with_blockfrost_utxos(recipients, sender_address, selected_utxos, blockfrost_api_key)
    
    else:
        print(f"⚠️  No Blockfrost API key provided")
        return create_manual_utxo_instructions(recipients, sender_address, total_needed)

def build_transaction_with_blockfrost_utxos(
    recipients: List[Dict[str, str]], 
    sender_address: str, 
    utxos_data: List[Dict],
    api_key: str
) -> str:
    """Build transaction using real UTXOs from Blockfrost."""
    
    try:
        # Create Blockfrost context
        context = BlockFrostChainContext(api_key, Network.MAINNET)
        
        # Create transaction builder
        builder = TransactionBuilder(context)
        
        # Parse sender address
        sender_addr = Address.decode(sender_address)
        
        # Add real UTXOs as inputs
        for utxo_data in utxos_data:
            tx_hash = utxo_data['tx_hash']
            output_index = utxo_data['output_index']
            
            # Create transaction input
            tx_input = TransactionInput.from_primitive([tx_hash, output_index])
            
            # Create UTXO value
            lovelace_amount = int(utxo_data['amount'][0]['quantity'])
            utxo_value = Value(lovelace_amount)
            
            # Create UTXO output
            utxo_output = TransactionOutput(sender_addr, utxo_value)
            
            # Create UTXO
            utxo = UTxO(tx_input, utxo_output)
            
            # Add to builder
            builder.add_input(utxo)
        
        # Add recipient outputs
        for recipient in recipients:
            recipient_addr = Address.decode(recipient['address'])
            amount_lovelace = ada_to_lovelace(recipient['ada_amount'])
            output = TransactionOutput(recipient_addr, Value(amount_lovelace))
            builder.add_output(output)
        
        # Add metadata
        metadata = {
            674: {
                "msg": ["BOM Airdrop S1 - Real UTXOs"],
                "recipients": str(len(recipients)),
                "total_ada": str(sum(r['ada_amount'] for r in recipients))
            }
        }
        
        auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
        builder.auxiliary_data = auxiliary_data
        
        # Build transaction
        tx = builder.build()
        
        print(f"✅ Real transaction built!")
        print(f"   Transaction ID: {tx.id}")
        print(f"   Inputs: {len(utxos_data)} real UTXOs")
        print(f"   Outputs: {len(recipients)} recipients")
        
        return tx.to_cbor().hex()
        
    except Exception as e:
        print(f"❌ Error building real transaction: {e}")
        return create_manual_utxo_instructions(recipients, sender_address, 0)

def create_manual_utxo_instructions(recipients: List[Dict[str, str]], sender_address: str, total_needed: int) -> str:
    """Create instructions for manually getting UTXOs."""
    
    total_ada = sum(r['ada_amount'] for r in recipients)
    
    instructions = {
        "error": "Cannot create signable transaction without real UTXOs",
        "problem": "Eternl needs to see UTXOs from your actual wallet to sign the transaction",
        "solution": "Get a Blockfrost API key to query real UTXOs",
        "steps": [
            "1. Go to https://blockfrost.io and create a free account",
            "2. Create a new project and get your project ID (API key)",
            "3. Run this script again with the API key",
            "4. The script will query your real UTXOs and build a signable transaction"
        ],
        "transaction_details": {
            "sender": sender_address,
            "recipients": len(recipients),
            "total_ada_needed": total_ada,
            "total_lovelace_needed": ada_to_lovelace(total_ada),
            "recipients_list": [
                {
                    "address": r['address'],
                    "ada_amount": r['ada_amount']
                }
                for r in recipients
            ]
        },
        "alternative_solutions": [
            "Use cardano-cli to build the transaction manually",
            "Use a different wallet that can import partial transactions",
            "Export UTXOs from Eternl and provide them to this script"
        ]
    }
    
    # Save instructions
    with open("data/UTXO_INSTRUCTIONS.json", 'w') as f:
        json.dump(instructions, f, indent=2)
    
    print(f"📋 Instructions saved to: data/UTXO_INSTRUCTIONS.json")
    
    return json.dumps(instructions, indent=2)

def create_instructions_file(sender_address: str):
    """Create instructions file for getting API key."""
    instructions = {
        "next_steps": [
            "1. Go to https://blockfrost.io",
            "2. Create a free account",
            "3. Create a new project",
            "4. Copy your project ID",
            "5. Run this script again with your project ID"
        ],
        "wallet_address": sender_address,
        "status": "NEEDS_API_KEY"
    }
    
    with open("data/UTXO_INSTRUCTIONS.json", 'w') as f:
        json.dump(instructions, f, indent=2)
    
    print(f"📋 Instructions saved to: data/UTXO_INSTRUCTIONS.json")
    return instructions

def main():
    print("🔧 Real UTXO Transaction Builder for Eternl")
    print("=" * 50)
    
    # Get configuration
    sender_address = input("Enter your wallet address: ").strip()
    if not sender_address.startswith('addr1'):
        print("❌ Invalid address format")
        return
    
    print("\n📡 Do you have a Blockfrost API key?")
    print("1. Yes - I have a Blockfrost API key")
    print("2. No - I need instructions to get one")
    
    choice = input("Choose (1/2): ").strip()
    
    if choice == "1":
        api_key = input("Enter your Blockfrost project ID: ").strip()
        if not api_key:
            api_key = None
    else:
        api_key = None
        print("📝 Will provide instructions to get API key")
    
    # Read recipients
    csv_file = "data/BOM-Airdrop-S1-Clean.csv"
    recipients = read_airdrop_data(csv_file, 10)
    
    print(f"\n📋 Transaction Summary:")
    print(f"   Sender: {sender_address[:25]}...{sender_address[-15:]}")
    print(f"   Recipients: {len(recipients)}")
    print(f"   Total ADA: {sum(r['ada_amount'] for r in recipients):.2f}")
    print()
    
    # Create transaction
    result = create_transaction_with_real_utxos(recipients, sender_address, api_key)
    
    if result.startswith('{'):
        # JSON instructions
        print("📋 Check data/UTXO_INSTRUCTIONS.json for next steps")
    else:
        # CBOR hex
        print(f"✅ CBOR generated with REAL UTXOs!")
        
        # Save Eternl file
        eternl_tx = {
            "type": "Tx ConwayEra",
            "description": f"BOM Airdrop S1 - {len(recipients)} Recipients - REAL UTXOs",
            "cborHex": result
        }
        
        with open("data/airdrop_REAL_UTXOS_eternl.json", 'w') as f:
            json.dump(eternl_tx, f, indent=2)
        
        print(f"📱 Import: data/airdrop_REAL_UTXOS_eternl.json")
        print(f"🎯 This transaction uses YOUR real UTXOs - Eternl will recognize it!")

if __name__ == "__main__":
    main() 