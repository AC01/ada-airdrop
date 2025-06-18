# Staking Results Processor

This project processes staking data for different seasons and generates comprehensive results CSV files that match the format used for Season 1.

## Features

- Processes user data, wallets, balances, and promises
- Calculates combo bonuses from snapshot data
- Generates Seer and Heroes reward columns
- Can be easily adapted for future seasons
- Comprehensive error handling and logging
- Statistical analysis including completion rates and rankings

## Files

- `season_2_processor.py` - Main processor script with Season2Processor class
- `staking_season_2_results.csv` - Generated Season 2 results
- `season_comparison_report.md` - Comparison report between seasons
- `data/` - Directory containing all CSV data files

## Data Files

- `snapshot_user_data.csv` - Daily PSTG tracking with sources for combo bonuses, Seer rewards, and Heroes rewards
- `user_balances.csv` - Final PSTG balances for Season 2
- `staking_season_end.csv` - Season 1 results for comparison
- `users.csv` - User IDs and Discord names mapping
- `user_wallets.csv` - Wallet addresses and verification data
- `user_primary_wallet.csv` - Primary wallet mappings by user ID
- `staking_promises.csv` - Promise/staking data per user with completion status

## Usage

```python
from season_2_processor import Season2Processor

# Initialize processor
processor = Season2Processor()

# Run the complete processing pipeline
processor.run()
```

## Output Columns

- Basic info: rank, account_id, username, nickname, wallet_address
- Financial: final_pstg, ada_value, total_bonus_rewards
- Promises: total_promises, completed_promises, broken_promises, promise_completion_rate
- Rewards: combo_bonus_pstg, seer_rewards, heroes_rewards, staking_rewards
- Flags: has_promises, perfect_promises
- Metadata: season, processed_date

## Season Adaptability

The processor is designed to be season-agnostic. To process a different season:

1. Update the `season` parameter in the constructor
2. Ensure the data files contain the appropriate season data
3. Run the processor

The framework automatically filters data by season and generates appropriate results. 