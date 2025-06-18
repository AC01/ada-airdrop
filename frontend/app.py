import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
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
    BlockFrostChainContext,
    AuxiliaryData,
    Metadata
)

# Configure Streamlit page
st.set_page_config(
    page_title="Cardano Airdrop Generator",
    page_icon="🚀",
    layout="wide"
)

def ada_to_lovelace(ada_amount: float) -> int:
    """Convert ADA to Lovelace."""
    return int(ada_amount * 1_000_000)

def validate_csv(df):
    """Validate the CSV format."""
    required_columns = ['Address', 'ADA Value']
    
    # Check columns exist
    if not all(col in df.columns for col in required_columns):
        return False, "CSV must contain 'Address' and 'ADA Value' columns"
    
    # Validate addresses
    invalid_addresses = [addr for addr in df['Address'] if not str(addr).startswith('addr1')]
    if invalid_addresses:
        return False, f"Found {len(invalid_addresses)} invalid addresses. All addresses must start with 'addr1'"
    
    # Validate ADA amounts
    try:
        df['ADA Value'] = pd.to_numeric(df['ADA Value'])
        if (df['ADA Value'] <= 0).any():
            return False, "All ADA values must be positive"
    except:
        return False, "ADA Value column must contain valid numbers"
    
    return True, "CSV validation passed"

def create_transaction(blockfrost_id, wallet_address, recipients_df, num_recipients=None, metadata_message=None):
    """Create the transaction using PyCardano."""
    try:
        # Initialize BlockFrost context
        context = BlockFrostChainContext(
            project_id=blockfrost_id,
            network=Network.MAINNET
        )
        
        # Parse sender address
        sender_addr = Address.from_primitive(wallet_address)
        
        # Get UTXOs
        utxos = context.utxos(sender_addr)
        if not utxos:
            return False, "No UTXOs found for this wallet address"
        
        # Prepare recipients
        if num_recipients:
            recipients_df = recipients_df.head(num_recipients)
        
        recipients = [
            {
                'address': row['Address'].strip(),
                'ada_amount': float(row['ADA Value'])
            }
            for _, row in recipients_df.iterrows()
        ]
        
        # Calculate totals
        total_ada = sum(r['ada_amount'] for r in recipients)
        total_lovelace = sum(ada_to_lovelace(r['ada_amount']) for r in recipients)
        estimated_fee = 500000  # Fixed fee: 0.5 ADA
        total_needed = total_lovelace + estimated_fee
        
        # Select UTXOs
        utxos.sort(key=lambda utxo: utxo.output.amount.coin, reverse=True)
        selected_utxos = []
        total_selected = 0
        for utxo in utxos:
            selected_utxos.append(utxo)
            total_selected += utxo.output.amount.coin
            if total_selected >= total_needed:
                break
        
        if total_selected < total_needed:
            return False, f"Insufficient funds. Need {total_needed / 1_000_000:.2f} ADA, have {total_selected / 1_000_000:.2f} ADA"
        
        # Create transaction inputs
        tx_inputs = [TransactionInput(utxo.input.transaction_id, utxo.input.index) for utxo in selected_utxos]
        
        # Create outputs
        tx_outputs = []
        for recipient in recipients:
            output = TransactionOutput(
                address=Address.from_primitive(recipient['address']),
                amount=Value(coin=ada_to_lovelace(recipient['ada_amount']))
            )
            tx_outputs.append(output)
        
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
            else:
                change_value = Value(coin=change_amount)
            
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

        # Add metadata if provided
        auxiliary_data = None
        if metadata_message:
            metadata = {
                674: {  # Using 674 as an example label
                    "msg": metadata_message
                }
            }
            auxiliary_data = AuxiliaryData(Metadata(metadata))
            # Create metadata hash and add it to transaction body
            tx_body.auxiliary_data_hash = auxiliary_data.hash()
        
        # Create transaction with metadata
        transaction = Transaction(
            transaction_body=tx_body,
            transaction_witness_set=TransactionWitnessSet(),
            auxiliary_data=auxiliary_data
        )
        
        # Generate and validate CBOR
        cbor_hex = transaction.to_cbor().hex()
        test_tx = Transaction.from_cbor(cbor_hex)
        
        # Create Eternl file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eternl_data = {
            "type": "Tx ConwayEra",
            "description": f"BOM Airdrop - {len(recipients)} Recipients ({total_ada:.2f} ADA)",
            "cborHex": cbor_hex
        }
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save files
        filename = output_dir / f"airdrop_eternl_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(eternl_data, f, indent=2)
        
        # Create summary of tokens found
        token_summary = []
        for policy_id, assets in total_tokens.items():
            for asset_name, quantity in assets.items():
                asset_name_hex = asset_name.payload.hex() if hasattr(asset_name, 'payload') else str(asset_name)
                token_summary.append({
                    'policy_id': str(policy_id),
                    'asset_name': asset_name_hex,
                    'quantity': quantity
                })

        return True, {
            'filename': str(filename),
            'transaction_id': transaction.id,
            'num_inputs': len(tx_inputs),
            'num_outputs': len(tx_outputs),
            'total_ada': total_ada,
            'fee': estimated_fee / 1_000_000,
            'change': change_amount / 1_000_000,
            'tokens_found': len(token_summary),
            'token_details': token_summary
        }
        
    except Exception as e:
        return False, f"Error creating transaction: {str(e)}"

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Blockfrost ID
    blockfrost_id = st.text_input(
        "Blockfrost Project ID",
        help="Your Blockfrost API key (starts with 'mainnet')",
        type="password"
    )
    
    # Wallet address
    wallet_address = st.text_input(
        "Wallet Address",
        help="Your wallet address (starts with 'addr1')"
    )
    
    # Number of recipients
    num_recipients = st.number_input(
        "Number of Recipients",
        min_value=1,
        max_value=1000,
        value=5,
        help="Number of recipients to process from the CSV"
    )

    # Metadata message
    metadata_message = st.text_area(
        "Transaction Metadata",
        help="Optional message to include in the transaction metadata",
        placeholder="Enter your message here..."
    )
    
    # Save settings
    if st.button("💾 Save Settings"):
        st.session_state.blockfrost_id = blockfrost_id
        st.session_state.wallet_address = wallet_address
        st.success("Settings saved!")

# Main content
st.title("🚀 Cardano Airdrop Generator")
st.write("Generate Eternl-compatible transaction files for airdrops")

# File upload
uploaded_file = st.file_uploader(
    "Upload CSV file",
    type="csv",
    help="CSV file with columns: Address, ADA Value"
)

if uploaded_file:
    # Read and validate CSV
    df = pd.read_csv(uploaded_file)
    is_valid, message = validate_csv(df)
    
    if is_valid:
        st.success("✅ CSV validation passed")
        
        # Display preview
        st.subheader("📊 Data Preview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Recipients", len(df))
        with col2:
            st.metric("Total ADA", f"{df['ADA Value'].sum():.2f}")
        with col3:
            st.metric("Processing", num_recipients)
        
        # Show full dataset
        st.subheader("📋 Full Dataset")
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "Address": st.column_config.TextColumn("Recipient Address"),
                "ADA Value": st.column_config.NumberColumn("ADA Amount", format="%.2f")
            }
        )
        
        # Show subset that will be processed
        st.subheader(f"🎯 Processing First {num_recipients} Recipients")
        subset_df = df.head(num_recipients)
        st.dataframe(
            subset_df,
            hide_index=True,
            column_config={
                "Address": st.column_config.TextColumn("Recipient Address"),
                "ADA Value": st.column_config.NumberColumn("ADA Amount", format="%.5f")
            }
        )
        st.metric("Subset Total ADA", f"{subset_df['ADA Value'].sum():.2f}")

        # Check for outputs below minimum ADA
        MIN_ADA_PER_OUTPUT = 0.96975
        too_small = subset_df[subset_df['ADA Value'] < MIN_ADA_PER_OUTPUT]
        if not too_small.empty:
            st.error(f"❌ {len(too_small)} outputs are below the Cardano minimum of {MIN_ADA_PER_OUTPUT} ADA per output. Please fix your CSV.")
            st.dataframe(too_small, hide_index=True)
        
        # Show metadata preview if provided
        if metadata_message and metadata_message.strip():
            st.subheader("📝 Metadata Preview")
            metadata_preview = {
                "label": "674",
                "metadata": {
                    "msg": metadata_message.strip()
                }
            }
            st.json(metadata_preview)
        
        # Generate transaction
        if st.button("🔥 Generate Transaction"):
            if not blockfrost_id or not wallet_address:
                st.error("Please enter Blockfrost ID and wallet address in the sidebar")
            elif not too_small.empty:
                st.error(f"Cannot generate transaction: {len(too_small)} outputs are below the minimum ADA per output.")
            else:
                with st.spinner("Generating transaction..."):
                    success, result = create_transaction(
                        blockfrost_id,
                        wallet_address,
                        df,
                        num_recipients,
                        metadata_message if metadata_message.strip() else None
                    )
                
                if success:
                    st.success("✅ Transaction generated successfully!")
                    
                    # Display transaction details
                    st.subheader("📝 Transaction Details")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Recipients", result['num_outputs'] - 1)  # Subtract change output
                        st.metric("Total ADA", f"{result['total_ada']:.2f}")
                    with col2:
                        st.metric("Inputs", result['num_inputs'])
                        st.metric("Fee", f"{result['fee']:.6f}")
                    with col3:
                        st.metric("Outputs", result['num_outputs'])
                        st.metric("Change", f"{result['change']:.6f}")
                    
                    st.code(f"Transaction ID: {result['transaction_id']}")
                    
                    # Show token/NFT information if any were found
                    if result.get('tokens_found', 0) > 0:
                        st.subheader("🪙 Tokens/NFTs in Change Output")
                        st.info(f"Found {result['tokens_found']} token(s)/NFT(s) that will be returned to your wallet in the change output.")
                        
                        # Display token details in a table
                        if result.get('token_details'):
                            token_df = pd.DataFrame(result['token_details'])
                            token_df['short_policy'] = token_df['policy_id'].str[:20] + "..."
                            token_df['short_asset'] = token_df['asset_name'].str[:20] + "..."
                            
                            st.dataframe(
                                token_df[['short_policy', 'short_asset', 'quantity']],
                                hide_index=True,
                                column_config={
                                    "short_policy": st.column_config.TextColumn("Policy ID"),
                                    "short_asset": st.column_config.TextColumn("Asset Name"),
                                    "quantity": st.column_config.NumberColumn("Quantity")
                                }
                            )
                    else:
                        st.info("ℹ️ No tokens/NFTs found in your UTXOs - only ADA will be processed.")
                    
                    # Download button
                    with open(result['filename'], 'r') as f:
                        st.download_button(
                            "📥 Download Eternl Transaction",
                            f.read(),
                            file_name=os.path.basename(result['filename']),
                            mime="application/json",
                            help="Import this file into Eternl wallet"
                        )
                    
                    # Instructions
                    st.subheader("📋 Next Steps")
                    st.write("""
                    1. Download the transaction file
                    2. Open Eternl wallet
                    3. Go to Transaction Importer
                    4. Import the downloaded file
                    5. Review all details carefully
                    6. Sign and submit the transaction
                    """)
                else:
                    st.error(f"❌ {result}")
    else:
        st.error(f"❌ {message}")

# Disclaimer
st.divider()
st.warning("""
⚠️ **IMPORTANT DISCLAIMER - BETA SOFTWARE**

🔶 **This is beta testing software** - Use at your own risk  
🔶 **User Responsibility**: You are solely responsible for verifying all transaction details before signing  
🔶 **No Liability**: The developers assume no responsibility for any errors, losses, or damages  
🔶 **Always Verify**: Double-check recipient addresses, amounts, and fees before submitting  
🔶 **Test First**: Test with small amounts before processing large transactions  
🔶 **No Guarantees**: This software is provided "as-is" without warranties of any kind  

By using this tool, you acknowledge these risks and accept full responsibility for your transactions.
""")

# Footer
st.divider()
st.caption("Made with ❤️ using PyCardano and Streamlit | Developed by [Ash](https://x.com/AshleyCNFT)") 