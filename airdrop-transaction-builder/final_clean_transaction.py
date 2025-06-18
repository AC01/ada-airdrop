#!/usr/bin/env python3
"""
Create a final clean transaction for Eternl wallet.
This script uses real UTXOs and proper CBOR formatting with token/NFT support.
"""

import json
import csv
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
    Network,
    BlockFrostChainContext
)

def ada_to_lovelace(ada_amount: float) -> int:
    """Convert ADA to Lovelace."""
    return int(ada_amount * 1_000_000)

def create_final_transaction():
    """Create a final clean transaction for Eternl."""
    
    # Get sender address
    print("\n💳 Enter your wallet address")
    print("This is the address that contains the UTXOs to spend")
    sender_address = input("Address (starts with addr1): ").strip()
    
    if not sender_address.startswith('addr1'):
        print("❌ Invalid address format. Must start with 'addr1'")
        return None
    
    # Read recipient data
    recipients = []
    try:
        with open('data/BOM-Airdrop-S1-Clean.csv', 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 5:  # Only process first 5 rows
                    break
                recipients.append({
                    'address': row['address'].strip(),
                    'ada_amount': float(row['ADA Value'])
                })
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return None
    
    total_ada = sum(r['ada_amount'] for r in recipients)
    print(f"📋 Recipients: {len(recipients)}")
    print(f"💰 Total ADA: {total_ada:.2f}")
    
    # Initialize BlockFrost context
    try:
        context = BlockFrostChainContext(
            project_id="mainnetZh9t5uEdHlNSa449YdXLAzxJTONs5ucl",
            network=Network.MAINNET
        )
    except Exception as e:
        print(f"❌ Failed to initialize BlockFrost: {e}")
        return None
    
    # Parse sender address
    try:
        sender_addr = Address.from_primitive(sender_address)
    except Exception as e:
        print(f"❌ Failed to parse sender address: {e}")
        return None
    
    print("\n🔍 Querying UTXOs...")
    utxos = context.utxos(sender_addr)
    print(f"✅ Found {len(utxos)} UTXOs")
    
    if not utxos:
        print("❌ No UTXOs found for this address")
        print("   Please check the address is correct")
        return None
    
    # Calculate total needed amount including estimated fee
    total_lovelace = sum(ada_to_lovelace(r['ada_amount']) for r in recipients)
    estimated_fee = 300000  # Initial fee estimate
    total_needed = total_lovelace + estimated_fee
    
    # Sort UTXOs by amount
    utxos.sort(key=lambda utxo: utxo.output.amount.coin, reverse=True)
    
    # Select UTXOs
    selected_utxos = []
    total_selected = 0
    for utxo in utxos:
        selected_utxos.append(utxo)
        total_selected += utxo.output.amount.coin
        if total_selected >= total_needed:
            break
    
    if total_selected < total_needed:
        print(f"❌ Insufficient funds in wallet")
        print(f"   Need: {total_needed / 1_000_000:.2f} ADA")
        print(f"   Have: {total_selected / 1_000_000:.2f} ADA")
        return None
    
    print(f"\n💰 Selected {len(selected_utxos)} UTXOs")
    print(f"   Total value: {total_selected / 1_000_000:.2f} ADA")
    
    # Create transaction inputs
    tx_inputs = [TransactionInput(utxo.input.transaction_id, utxo.input.index) for utxo in selected_utxos]
    
    # Create outputs for each recipient
    tx_outputs = []
    for recipient in recipients:
        output = TransactionOutput(
            address=Address.from_primitive(recipient['address']),
            amount=Value(coin=ada_to_lovelace(recipient['ada_amount']))
        )
        tx_outputs.append(output)
        print(f"✅ Added output: {recipient['ada_amount']:.6f} ADA -> {recipient['address'][:20]}...")
    
    # Calculate change - including tokens/NFTs from selected UTXOs
    change_amount = total_selected - total_lovelace - estimated_fee
    
    # Collect all tokens/NFTs from selected UTXOs
    total_tokens = {}
    for utxo in selected_utxos:
        if utxo.output.amount.multi_asset:
            for policy_id, assets in utxo.output.amount.multi_asset.items():
                if policy_id not in total_tokens:
                    total_tokens[policy_id] = {}
                for asset_name, quantity in assets.items():
                    if asset_name not in total_tokens[policy_id]:
                        total_tokens[policy_id][asset_name] = 0
                    total_tokens[policy_id][asset_name] += quantity

    # Create change output with ADA and tokens/NFTs
    if change_amount > 0 or total_tokens:
        # Build the Value object for change
        if total_tokens:
            # Create MultiAsset from collected tokens
            from pycardano import MultiAsset, Asset
            multi_asset = MultiAsset()
            for policy_id, assets in total_tokens.items():
                # Create Asset object for this policy
                asset_obj = Asset()
                for asset_name, quantity in assets.items():
                    asset_obj[asset_name] = quantity
                multi_asset[policy_id] = asset_obj
            
            change_value = Value(coin=max(change_amount, 0), multi_asset=multi_asset)
            print(f"✅ Added change output: {change_amount / 1_000_000:.6f} ADA + {len(total_tokens)} token types")
        else:
            change_value = Value(coin=change_amount)
            print(f"✅ Added change output: {change_amount / 1_000_000:.6f} ADA")
        
        change_output = TransactionOutput(
            address=sender_addr,
            amount=change_value
        )
        tx_outputs.append(change_output)
    
    # Create transaction body
    tx_body = TransactionBody(
        inputs=tx_inputs,
        outputs=tx_outputs,
        fee=estimated_fee
    )
    
    # Create proper witness set (empty for unsigned transaction)
    witness_set = TransactionWitnessSet()
    
    # Create the transaction
    transaction = Transaction(
        transaction_body=tx_body,
        transaction_witness_set=witness_set
    )
    
    print(f"\n✅ Transaction constructed:")
    print(f"   Transaction ID: {transaction.id}")
    print(f"   Inputs: {len(tx_body.inputs)}")
    print(f"   Outputs: {len(tx_body.outputs)}")
    print(f"   Fee: {tx_body.fee / 1_000_000:.6f} ADA")
    
    # Generate CBOR
    cbor_hex = transaction.to_cbor().hex()
    print(f"   CBOR length: {len(cbor_hex)} characters")
    
    # Validate CBOR by parsing it back
    try:
        test_tx = Transaction.from_cbor(cbor_hex)
        print(f"✅ CBOR validation successful!")
        print(f"   Parsed transaction ID: {test_tx.id}")
    except Exception as e:
        print(f"❌ CBOR validation failed: {e}")
        return None
    
    # Create Eternl import file
    eternl_data = {
        "type": "Tx ConwayEra",
        "description": f"BOM Airdrop S1 - {len(recipients)} Recipients ({total_ada:.2f} ADA)",
        "cborHex": cbor_hex
    }
    
    # Save to file
    filename = "data/airdrop_FINAL_eternl.json"
    with open(filename, 'w') as f:
        json.dump(eternl_data, f, indent=2)
    
    print(f"💾 Saved: {filename}")
    return filename

def main():
    print("🎯 Creating Final Clean Transaction")
    print("=" * 40)
    
    filename = create_final_transaction()
    
    if filename:
        print(f"\n🎉 SUCCESS!")
        print(f"📁 Import this file into Eternl: {filename}")
        print(f"   ✅ Proper CBOR array structure")
        print(f"   ✅ Valid TransactionWitnessSet")
        print(f"   ✅ Passes CBOR validation")
        print(f"   ✅ Uses real UTXOs")
        print(f"   ✅ Handles tokens/NFTs properly")
        
        print(f"\n💡 Instructions:")
        print(f"   1. Open Eternl wallet")
        print(f"   2. Go to Transaction Importer")
        print(f"   3. Import {filename}")
        print(f"   4. Review and sign the transaction")
    else:
        print(f"\n❌ Failed to create final transaction")

if __name__ == "__main__":
    main() 