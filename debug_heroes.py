import pandas as pd
import json

# Load snapshot data
snapshot_data = pd.read_csv('data/snapshot_user_data.csv')
user_snapshots = snapshot_data[snapshot_data['account_id'] == 118]

total_heroes = 0
for _, record in user_snapshots.iterrows():
    try:
        snapshot_json = json.loads(record['snapshot_data'])
        rewards = snapshot_json.get('rewards', {})
        heroes_list = rewards.get('heroes', [])
        for hero in heroes_list:
            if isinstance(hero, dict):
                hero_pstg = hero.get('pstg', 0)
                total_heroes += hero_pstg
                print(f'Found hero with pstg: {hero_pstg}')
    except Exception as e:
        print(f'Error: {e}')

print(f'Total heroes for user 118: {total_heroes}') 