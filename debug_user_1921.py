import pandas as pd
import json

# Load snapshot data
snapshot_data = pd.read_csv('data/snapshot_user_data.csv')
user_snapshots = snapshot_data[snapshot_data['account_id'] == 1921]

print(f"User 1921 (invictusknights) Analysis")
print(f"Total snapshot records: {len(user_snapshots)}")

# From the results CSV we know:
# Actual balance: 5,614,493
# Expected balance: 5,628,313  
# Difference: -13,820 (actual is 13,820 LESS than expected)

print(f"\nFrom results CSV:")
print(f"Actual balance: 5,614,493")
print(f"Expected balance: 5,628,313")
print(f"Difference: -13,820")

total_heroes = 0
total_combo = 0
total_seer = 0
total_staking = 0

# Parse all snapshot records
for idx, record in user_snapshots.iterrows():
    try:
        snapshot_json = json.loads(record['snapshot_data'])
        rewards = snapshot_json.get('rewards', {})
        
        # Heroes rewards
        heroes_list = rewards.get('heroes', [])
        for hero in heroes_list:
            if isinstance(hero, dict):
                total_heroes += hero.get('pstg', 0)
        
        # Combo bonuses
        bonus_list = rewards.get('bonus', [])
        for bonus in bonus_list:
            total_combo += bonus.get('value', 0)
        
        # Seer rewards
        seer_list = rewards.get('seer', [])
        for seer in seer_list:
            total_seer += seer.get('card_1_base_pstg', 0) + seer.get('card_1_bonus_pstg', 0)
            total_seer += seer.get('card_2_base_pstg', 0) + seer.get('card_2_bonus_pstg', 0)
            total_seer += seer.get('card_3_base_pstg', 0) + seer.get('card_3_bonus_pstg', 0)
        
        # Staking rewards
        staking_list = rewards.get('staking', [])
        for stake in staking_list:
            total_staking += int(stake.get('pstg', 0))
            
    except Exception as e:
        print(f'Error processing record {idx}: {e}')

print(f"\nSnapshot reward totals:")
print(f"Heroes: {total_heroes:,}")
print(f"Combo bonuses: {total_combo:,}")
print(f"Seer: {total_seer:,}")
print(f"Staking: {total_staking:,}")

# From promises we know they earned 3,986,393
promise_value = 3986393
print(f"Promise value: {promise_value:,}")

calculated_expected = promise_value + total_combo + total_seer + total_heroes + total_staking
print(f"\nCalculated expected balance: {calculated_expected:,}")
print(f"Actual balance: 5,614,493")
print(f"Difference: {5614493 - calculated_expected:,}")

print(f"\nBreakdown:")
print(f"Promises: {promise_value:,}")
print(f"Staking: {total_staking:,}")
print(f"Combo: {total_combo:,}")
print(f"Seer: {total_seer:,}")
print(f"Heroes: {total_heroes:,}")
print(f"Total: {calculated_expected:,}") 