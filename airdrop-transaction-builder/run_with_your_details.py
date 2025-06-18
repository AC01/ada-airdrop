#!/usr/bin/env python3
"""
Run the UTXO transaction builder with user's specific details.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.getcwd())

# Import our UTXO transaction functions
from generate_real_utxo_tx import read_airdrop_data, create_transaction_with_real_utxos
import json

def main():
    print("🚀 Building Transaction with Your Real UTXOs")
    print("=" * 50)
    
    # Your details
    sender_address = "addr1q9m38fr5e92hqe86yf7wm28gykvnws8zhhemszn7g0ej3x6ruqlpn76nxjy7cczcwvgl8qdxq3saz8tav2axvwfptvxq268ul9"
    blockfrost_api_key = "mainnetZh9t5uEdHlNSa449YdXLAzxJTONs5ucl"
    
    print(f"👤 Your Address: {sender_address[:30]}...{sender_address[-15:]}")
    print(f"🔑 API Key: {blockfrost_api_key[:10]}...{blockfrost_api_key[-5:]}")
    print()
    
    # Read recipients from CSV
    csv_file = "csv/BOM-Airdrop-S1-Clean.csv"
    recipients = read_airdrop_data(csv_file, 5)
    
    print(f"📋 Transaction Summary:")
    print(f"   Recipients: {len(recipients)}")
    print(f"   Total ADA: {sum(r['ada_amount'] for r in recipients):.2f}")
    
    for i, recipient in enumerate(recipients, 1):
        print(f"   {i}. {recipient['address'][:25]}...{recipient['address'][-15:]} - {recipient['ada_amount']:.2f} ADA")
    print()
    
    # Create transaction with real UTXOs
    try:
        result = create_transaction_with_real_utxos(recipients, sender_address, blockfrost_api_key)
        
        if result.startswith('{'):
            # JSON instructions
            print("📋 Instructions saved to csv/UTXO_INSTRUCTIONS.json")
        else:
            # CBOR hex
            print(f"✅ SUCCESS! CBOR generated with YOUR REAL UTXOs!")
            
            # Save Eternl file
            eternl_tx = {
                "type": "Tx ConwayEra", 
                "description": f"🎯 REAL BOM Airdrop S1 - {len(recipients)} Recipients - YOUR UTXOs",
                "cborHex": result
            }
            
            filename = "csv/airdrop_YOUR_REAL_UTXOS_eternl.json"
            with open(filename, 'w') as f:
                json.dump(eternl_tx, f, indent=2)
            
            print(f"📱 Eternl File: {filename}")
            print(f"🎯 This transaction uses YOUR real UTXOs!")
            print(f"💾 CBOR Length: {len(result)} characters")
            print()
            print(f"🔥 Import {filename} into Eternl - it will work this time!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Check your Blockfrost API key and network connection")

if __name__ == "__main__":
    main() 