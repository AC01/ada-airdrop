#!/usr/bin/env python3
"""
Test script to inspect tokens/NFTs in wallet UTXOs.
This helps debug the token handling before generating transactions.
"""

from pycardano import (
    Address,
    Network,
    BlockFrostChainContext
)

def inspect_wallet_tokens(wallet_address, blockfrost_id):
    """Inspect all tokens/NFTs in wallet UTXOs."""
    
    print(f"🔍 Inspecting wallet: {wallet_address[:20]}...{wallet_address[-15:]}")
    print("=" * 60)
    
    try:
        # Create context
        context = BlockFrostChainContext(
            project_id=blockfrost_id,
            network=Network.MAINNET
        )
        
        # Parse address
        sender_addr = Address.from_primitive(wallet_address)
        
        # Get UTXOs
        utxos = context.utxos(sender_addr)
        print(f"📦 Found {len(utxos)} UTXOs")
        
        if not utxos:
            print("❌ No UTXOs found!")
            return
        
        total_ada = 0
        total_tokens = {}
        
        for i, utxo in enumerate(utxos, 1):
            ada_amount = utxo.output.amount.coin / 1_000_000
            total_ada += ada_amount
            
            print(f"\n🎁 UTXO #{i}")
            print(f"   TX Hash: {utxo.input.transaction_id}")
            print(f"   Output Index: {utxo.input.index}")
            print(f"   ADA: {ada_amount:.6f}")
            
            # Check for tokens/NFTs
            if utxo.output.amount.multi_asset:
                print(f"   🪙 Contains tokens/NFTs:")
                
                for policy_id, assets in utxo.output.amount.multi_asset.items():
                    print(f"      Policy: {policy_id}")
                    
                    for asset_name, quantity in assets.items():
                        # Try to decode asset name
                        try:
                            if hasattr(asset_name, 'payload'):
                                asset_hex = asset_name.payload.hex()
                                # Try to decode as text
                                try:
                                    asset_text = bytes.fromhex(asset_hex).decode('utf-8')
                                    print(f"         • {asset_text} ({asset_hex}): {quantity}")
                                except:
                                    print(f"         • {asset_hex}: {quantity}")
                            else:
                                print(f"         • {asset_name}: {quantity}")
                        except:
                            print(f"         • {asset_name}: {quantity}")
                        
                        # Add to total
                        if policy_id not in total_tokens:
                            total_tokens[policy_id] = {}
                        if asset_name not in total_tokens[policy_id]:
                            total_tokens[policy_id][asset_name] = 0
                        total_tokens[policy_id][asset_name] += quantity
            else:
                print(f"   💰 ADA only (no tokens/NFTs)")
        
        print(f"\n📊 WALLET SUMMARY")
        print("=" * 30)
        print(f"Total ADA: {total_ada:.6f}")
        print(f"Total UTXOs: {len(utxos)}")
        
        if total_tokens:
            print(f"Token Types Found: {len(total_tokens)}")
            print(f"\n🪙 ALL TOKENS/NFTS:")
            
            for policy_id, assets in total_tokens.items():
                print(f"   Policy: {str(policy_id)[:20]}...{str(policy_id)[-15:]}")
                for asset_name, quantity in assets.items():
                    try:
                        if hasattr(asset_name, 'payload'):
                            asset_hex = asset_name.payload.hex()
                            try:
                                asset_text = bytes.fromhex(asset_hex).decode('utf-8')
                                print(f"      • {asset_text}: {quantity}")
                            except:
                                print(f"      • {asset_hex}: {quantity}")
                        else:
                            print(f"      • {asset_name}: {quantity}")
                    except:
                        print(f"      • {asset_name}: {quantity}")
        else:
            print(f"Tokens/NFTs: None (ADA only)")
        
        print(f"\n✅ Inspection complete!")
        
        # Warn about token handling
        if total_tokens:
            print(f"\n⚠️  IMPORTANT:")
            print(f"   Your wallet contains {len(total_tokens)} token type(s)")
            print(f"   The transaction builder will include these in the change output")
            print(f"   This prevents tokens from being accidentally burned")
        
        return utxos, total_tokens
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def main():
    print("🔍 Wallet Token Inspector")
    print("=" * 40)
    
    # Get user input
    wallet_address = input("Enter wallet address: ").strip()
    blockfrost_id = input("Enter Blockfrost project ID: ").strip()
    
    if not wallet_address or not blockfrost_id:
        print("❌ Both wallet address and Blockfrost ID are required")
        return
    
    # Inspect wallet
    utxos, tokens = inspect_wallet_tokens(wallet_address, blockfrost_id)
    
    if utxos:
        print(f"\n💡 This information helps ensure your transaction")
        print(f"   builder properly handles all assets in your wallet")

if __name__ == "__main__":
    main() 