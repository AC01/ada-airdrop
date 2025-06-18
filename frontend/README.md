# 🚀 Cardano Airdrop Generator Frontend

A user-friendly interface for generating Cardano airdrop transactions compatible with Eternl wallet.

## 🛠️ Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   cd frontend
   streamlit run app.py
   ```

## 📋 Features

- Clean, modern interface
- CSV validation and preview
- Real-time transaction generation
- Detailed transaction summary
- One-click download for Eternl
- Secure input handling
- Progress tracking
- Error handling and validation

## 💡 Usage

1. **Configure Settings** (Sidebar)
   - Enter your Blockfrost Project ID
   - Enter your wallet address
   - Set number of recipients to process

2. **Upload CSV**
   - Format: Address, ADA Value
   - Example:
     ```csv
     Address,ADA Value
     addr1q8...,1423.23
     addr1q9...,1032.96
     ```

3. **Generate Transaction**
   - Review the data preview
   - Click "Generate Transaction"
   - Download the Eternl-compatible file

4. **Import to Eternl**
   - Open Eternl wallet
   - Go to Transaction Importer
   - Import the downloaded file
   - Review and sign

## ⚠️ Important Notes

- Always verify transaction details before signing
- Keep your Blockfrost API key secure
- Test with small amounts first
- Ensure sufficient UTXOs for transaction fees

## 🔒 Security

- Blockfrost ID is stored securely
- No sensitive data is logged
- All processing happens locally
- No external API calls except Blockfrost 