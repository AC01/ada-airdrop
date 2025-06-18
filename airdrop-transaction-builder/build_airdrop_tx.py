#!/usr/bin/env python3
"""
Script to build CBOR transactions for Cardano airdrops using Eternl wallet format.
Takes the first 5 rows from BOM-Airdrop-S1-Clean.csv and builds a transaction.
"""

import csv
import json
from typing import List, Dict

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

def build_eternl_transaction(recipients: List[Dict[str, str]], description: str = "Airdrop Transaction - First 5 Recipients") -> Dict:
    """
    Build a transaction structure compatible with Eternl wallet.
    
    Note: This creates the JSON structure but the cborHex would need to be generated
    using a proper Cardano library like PyCardano or cardano-cli.
    """
    
    # Calculate total ADA being sent
    total_ada = sum(recipient['ada_amount'] for recipient in recipients)
    total_lovelace = ada_to_lovelace(total_ada)
    
    print(f"Building transaction for {len(recipients)} recipients")
    print(f"Total ADA to send: {total_ada:.2f} ADA ({total_lovelace:,} Lovelace)")
    print("\nRecipients:")
    for i, recipient in enumerate(recipients, 1):
        print(f"  {i}. {recipient['address'][:20]}...{recipient['address'][-10:]} - {recipient['ada_amount']:.2f} ADA")
    
    # This is a placeholder structure - the actual cborHex needs to be generated
    # using proper Cardano tooling
    transaction_structure = {
        "type": "Tx ConwayEra",
        "description": description,
        "cborHex": "PLACEHOLDER_CBOR_HEX_WOULD_GO_HERE_GENERATED_BY_CARDANO_TOOLING"
    }
    
    # Additional metadata for reference
    transaction_metadata = {
        "recipients": recipients,
        "total_ada": total_ada,
        "total_lovelace": total_lovelace,
        "recipient_count": len(recipients)
    }
    
    return transaction_structure, transaction_metadata

def main():
    # Read the first 5 rows from the CSV
    csv_file = "csv/BOM-Airdrop-S1-Clean.csv"
    recipients = read_airdrop_data(csv_file, 5)
    
    # Build the transaction structure
    tx_structure, metadata = build_eternl_transaction(recipients)
    
    # Save the transaction structure to a file
    output_file = "csv/airdrop_first_5_eternl_tx.json"
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(tx_structure, file, indent=2)
    
    # Save metadata for reference
    metadata_file = "csv/airdrop_first_5_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as file:
        json.dump(metadata, file, indent=2)
    
    print(f"\nTransaction structure saved to: {output_file}")
    print(f"Metadata saved to: {metadata_file}")
    
    print("\nNOTE: The cborHex field is a placeholder.")
    print("To generate the actual CBOR hex, you would need to use:")
    print("1. PyCardano library")
    print("2. cardano-cli")
    print("3. Or another Cardano transaction building tool")
    
    print(f"\nNext steps to complete the transaction:")
    print("1. Set up a Cardano node or use a service like Blockfrost")
    print("2. Query UTXOs for your sending wallet")
    print("3. Build the transaction with proper inputs/outputs")
    print("4. Generate the CBOR hex")
    print("5. Replace the placeholder in the JSON file")

if __name__ == "__main__":
    main() 