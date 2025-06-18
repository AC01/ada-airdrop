#!/usr/bin/env python3
"""
Season 2 Staking Results Processor

This script processes Season 2 staking data and generates a comprehensive results CSV
that matches the format used for Season 1 (staking_season_end.csv).

Key features:
- Processes user data, wallets, balances, and promises
- Calculates combo bonuses from snapshot data
- Generates Seer and Heroes reward columns
- Can be easily adapted for future seasons
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Season2Processor:
    def __init__(self, csv_dir='data'):
        self.csv_dir = csv_dir
        self.season = 2
        
        # Data containers
        self.users_df = None
        self.primary_wallets_df = None
        self.user_wallets_df = None
        self.balances_df = None
        self.promises_df = None
        self.snapshot_data = None
        
        # Results
        self.results_df = None
        
    def load_data(self):
        """Load all CSV files"""
        logger.info("Loading CSV data files...")
        
        try:
            # Load main data files
            self.users_df = pd.read_csv(os.path.join(self.csv_dir, 'users.csv'))
            self.primary_wallets_df = pd.read_csv(os.path.join(self.csv_dir, 'user_primary_wallet.csv'))
            self.user_wallets_df = pd.read_csv(os.path.join(self.csv_dir, 'user_wallets.csv'))
            self.balances_df = pd.read_csv(os.path.join(self.csv_dir, 'user_balances.csv'))
            self.promises_df = pd.read_csv(os.path.join(self.csv_dir, 'staking_promises.csv'))
            
            # Load snapshot data
            logger.info("Loading snapshot data...")
            self.snapshot_data = pd.read_csv(os.path.join(self.csv_dir, 'snapshot_user_data.csv'))
            
            # Filter balances for Season 2
            self.balances_df = self.balances_df[self.balances_df['season'] == self.season]
            
            logger.info(f"Loaded data for {len(self.users_df)} users")
            logger.info(f"Found {len(self.balances_df)} Season {self.season} balance records")
            logger.info(f"Found {len(self.promises_df)} promise records")
            logger.info(f"Found {len(self.snapshot_data)} snapshot records")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def get_user_wallet(self, account_id):
        """Get primary wallet address for a user, fallback to user_wallets if needed"""
        # First try primary wallet
        primary = self.primary_wallets_df[self.primary_wallets_df['account_id'] == account_id]
        if not primary.empty:
            wallet_id = primary.iloc[0]['user_wallet_id']
            wallet_record = self.user_wallets_df[self.user_wallets_df['id'] == wallet_id]
            if not wallet_record.empty:
                return wallet_record.iloc[0]['address0']
        
        # Fallback to any wallet for this user
        fallback = self.user_wallets_df[self.user_wallets_df['account_id'] == account_id]
        if not fallback.empty:
            return fallback.iloc[0]['address0']
        
        return None
    
    def calculate_promise_stats(self, account_id):
        """Calculate promise statistics for a user"""
        user_promises = self.promises_df[self.promises_df['account_id'] == account_id]
        
        if user_promises.empty:
            return {
                'total_promises': 0,
                'completed_promises': 0,
                'broken_promises': 0,
                'promise_completion_rate': 0,
                'total_promise_value': 0,
                'completed_promise_value': 0,
                # Promise length breakdowns
                'day_30_promises_made': 0,
                'day_30_promise_pstg_earned': 0,
                'day_90_promises_made': 0,
                'day_90_promise_pstg_earned': 0,
                'day_180_promises_made': 0,
                'day_180_promise_pstg_earned': 0,
                'rest_of_season_promises_made': 0,
                'rest_of_season_promise_pstg_earned': 0
            }
        
        completed = user_promises[user_promises['status'] == 'complete']
        broken = user_promises[user_promises['status'] == 'broken']
        
        total_promises = len(user_promises)
        completed_promises = len(completed)
        broken_promises = len(broken)
        
        completion_rate = (completed_promises / total_promises * 100) if total_promises > 0 else 0
        
        total_value = user_promises['promise_pstg_value'].sum()
        completed_value = completed['promise_pstg_value'].sum() if not completed.empty else 0
        
        # Calculate promise length breakdowns
        promise_stats = {
            'total_promises': total_promises,
            'completed_promises': completed_promises,
            'broken_promises': broken_promises,
            'promise_completion_rate': round(completion_rate, 2),
            'total_promise_value': total_value,
            'completed_promise_value': completed_value,
        }
        
        # Add length-specific statistics
        for length, col_suffix in [('30', 'day_30'), ('90', 'day_90'), ('180', 'day_180'), ('season', 'rest_of_season')]:
            length_promises = user_promises[user_promises['length'] == length]
            length_completed = length_promises[length_promises['status'] == 'complete']
            
            promise_stats[f'{col_suffix}_promises_made'] = len(length_promises)
            promise_stats[f'{col_suffix}_promise_pstg_earned'] = length_completed['promise_pstg_value'].sum() if not length_completed.empty else 0
        
        return promise_stats
    
    def parse_snapshot_rewards(self, account_id):
        """
        Parse snapshot data for combo bonuses, Seer rewards, Heroes rewards, and staking rewards
        """
        # Find all snapshot data for this user
        user_snapshots = self.snapshot_data[self.snapshot_data['account_id'] == account_id]
        
        if user_snapshots.empty:
            return 0, 0, 0, 0
        
        # Initialize totals
        total_combo = 0
        total_seer = 0
        total_heroes = 0
        total_staking = 0
        
        # Process each snapshot record for this user
        for _, record in user_snapshots.iterrows():
            try:
                # Parse the JSON data
                snapshot_json = json.loads(record['snapshot_data'])
                rewards = snapshot_json.get('rewards', {})
                
                # Sum combo bonus values
                bonus_list = rewards.get('bonus', [])
                for bonus in bonus_list:
                    total_combo += bonus.get('value', 0)
                
                # Sum seer values
                seer_list = rewards.get('seer', [])
                for seer in seer_list:
                    total_seer += seer.get('card_1_base_pstg', 0) + seer.get('card_1_bonus_pstg', 0)
                    total_seer += seer.get('card_2_base_pstg', 0) + seer.get('card_2_bonus_pstg', 0)
                    total_seer += seer.get('card_3_base_pstg', 0) + seer.get('card_3_bonus_pstg', 0)
                
                # Sum heroes values
                heroes_list = rewards.get('heroes', [])
                for hero in heroes_list:
                    # Heroes rewards use 'pstg' field, not 'value' like bonuses
                    if isinstance(hero, dict):
                        total_heroes += hero.get('pstg', 0)
                
                # Sum staking values
                staking_list = rewards.get('staking', [])
                for stake in staking_list:
                    total_staking += int(stake.get('pstg', 0))
                
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.warning(f"Error parsing snapshot data for user {account_id}: {e}")
                continue
        
        return total_combo, total_seer, total_heroes, total_staking
    
    def process_users(self):
        """Process all users and generate results"""
        logger.info("Processing user data...")
        
        results = []
        
        # Get all users who have Season 2 balances
        season_users = self.balances_df['account_id'].unique()
        
        for account_id in season_users:
            try:
                # Get user info
                user_info = self.users_df[self.users_df['id'] == account_id]
                if user_info.empty:
                    logger.warning(f"No user info found for account_id {account_id}")
                    continue
                
                user = user_info.iloc[0]
                
                # Get wallet address
                wallet_address = self.get_user_wallet(account_id)
                
                # Get balance
                balance_info = self.balances_df[self.balances_df['account_id'] == account_id]
                final_balance = balance_info.iloc[0]['balance'] if not balance_info.empty else 0
                
                # Calculate promise statistics
                promise_stats = self.calculate_promise_stats(account_id)
                
                # Parse snapshot data for rewards
                reward_data = self.parse_snapshot_rewards(account_id)
                
                # Compile user record
                user_record = {
                    'account_id': account_id,
                    'username': user['discord_username'],
                    'nickname': user.get('nickname', ''),
                    'wallet_address': wallet_address,
                    'current_balance': balance_info.iloc[0]['balance'] if not balance_info.empty else 0,
                    'final_pstg': final_balance,
                    'total_promises': promise_stats['total_promises'],
                    'completed_promises': promise_stats['completed_promises'],
                    'broken_promises': promise_stats['broken_promises'],
                    'promise_completion_rate': promise_stats['promise_completion_rate'],
                    'total_promise_value': promise_stats['total_promise_value'],
                    'completed_promise_value': promise_stats['completed_promise_value'],
                    'day_30_promises_made': promise_stats['day_30_promises_made'],
                    'day_30_promise_pstg_earned': promise_stats['day_30_promise_pstg_earned'],
                    'day_90_promises_made': promise_stats['day_90_promises_made'],
                    'day_90_promise_pstg_earned': promise_stats['day_90_promise_pstg_earned'],
                    'day_180_promises_made': promise_stats['day_180_promises_made'],
                    'day_180_promise_pstg_earned': promise_stats['day_180_promise_pstg_earned'],
                    'rest_of_season_promises_made': promise_stats['rest_of_season_promises_made'],
                    'rest_of_season_promise_pstg_earned': promise_stats['rest_of_season_promise_pstg_earned'],
                    'combo_bonus_pstg': reward_data[0],
                    'seer_rewards': reward_data[1],
                    'heroes_rewards': reward_data[2],
                    'staking_rewards': reward_data[3],
                    'season': self.season,
                    'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                results.append(user_record)
                
            except Exception as e:
                logger.error(f"Error processing user {account_id}: {e}")
                continue
        
        self.results_df = pd.DataFrame(results)
        logger.info(f"Processed {len(self.results_df)} users successfully")
    
    def add_ranking_and_stats(self):
        """Add ranking and additional statistics"""
        if self.results_df is None or self.results_df.empty:
            logger.error("No results to add rankings to")
            return
        
        # Calculate expected balance (sum of all reward types)
        self.results_df['expected_balance'] = (
            self.results_df['completed_promise_value'] + 
            self.results_df['combo_bonus_pstg'] + 
            self.results_df['seer_rewards'] + 
            self.results_df['heroes_rewards'] + 
            self.results_df['staking_rewards']
        )
        
        # Calculate balance difference for validation
        self.results_df['balance_difference'] = self.results_df['final_pstg'] - self.results_df['expected_balance']
        
        # Calculate ADA value proportionally
        total_pstg = self.results_df['final_pstg'].sum()
        total_ada_pool = 34798.58  # Season 2 ADA pool
        self.results_df['ada_value'] = (self.results_df['final_pstg'] / total_pstg) * total_ada_pool
        
        # Sort by final PSTG descending
        self.results_df = self.results_df.sort_values('final_pstg', ascending=False)
        
        # Add rank (season_rank)
        self.results_df['season_rank'] = range(1, len(self.results_df) + 1)
        
        # Rename columns to match required format
        self.results_df = self.results_df.rename(columns={
            'username': 'discord_username',
            'final_pstg': 'pstg_balance',
            'completed_promises': 'total_promises_from_user',  # Changed to use completed_promises instead of total_promises
            'completed_promise_value': 'total_promises_from_user_pstg_earned',
            'broken_promises': 'promises_broken',
            'staking_rewards': 'fluid_pstg_earned',
            'combo_bonus_pstg': 'combo_bonuses_pstg_earned'
        })
        
        # Add empty columns as specified
        self.results_df['next_season_chains_made'] = ''
        self.results_df['id'] = ''
        
        # Reorder columns to match exact specification
        column_order = [
            'account_id',
            'discord_username', 
            'pstg_balance',
            'expected_balance',
            'balance_difference',
            'ada_value',
            'season_rank',
            'wallet_address',
            'day_30_promises_made',
            'day_30_promise_pstg_earned',
            'day_90_promises_made', 
            'day_90_promise_pstg_earned',
            'day_180_promises_made',
            'day_180_promise_pstg_earned',
            'rest_of_season_promises_made',
            'rest_of_season_promise_pstg_earned',
            'total_promises_from_user',
            'total_promises_from_user_pstg_earned',
            'promises_broken',
            'fluid_pstg_earned',
            'combo_bonuses_pstg_earned',
            'next_season_chains_made',
            'seer_rewards',
            'heroes_rewards',
            'season',
            'id'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in column_order if col in self.results_df.columns]
        final_df = self.results_df[available_columns]
        
        try:
            final_df.to_csv(f'staking_season_{self.season}_results.csv', index=False)
            logger.info(f"Results saved to staking_season_{self.season}_results.csv")
            
            # Print summary statistics
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def print_summary(self):
        """Print summary statistics"""
        if self.results_df is None or self.results_df.empty:
            return
        
        print("\n" + "="*50)
        print(f"SEASON {self.season} STAKING RESULTS SUMMARY")
        print("="*50)
        print(f"Total Users: {len(self.results_df)}")
        print(f"Total PSTG in System: {self.results_df['pstg_balance'].sum():,.0f}")
        print(f"Average PSTG per User: {self.results_df['pstg_balance'].mean():,.0f}")
        print(f"Median PSTG: {self.results_df['pstg_balance'].median():,.0f}")
        print(f"Top Balance: {self.results_df['pstg_balance'].max():,.0f}")
        print()
        print(f"Total Promises Made: {self.results_df['total_promises_from_user'].sum()}")
        print(f"Total Promises Completed: {(self.results_df['total_promises_from_user'] - self.results_df['promises_broken']).sum()}")
        print(f"Overall Promise Completion Rate: {((self.results_df['total_promises_from_user'] - self.results_df['promises_broken']).sum() / self.results_df['total_promises_from_user'].sum() * 100):.2f}%")
        print()
        print(f"Total ADA Pool: {self.results_df['ada_value'].sum():,.2f}")
        print(f"Top ADA Earner: {self.results_df['ada_value'].max():,.2f}")
        print()
        print("BALANCE VALIDATION:")
        print(f"Users with Perfect Balance Match: {(self.results_df['balance_difference'] == 0).sum()}")
        print(f"Users with Balance Discrepancies: {(self.results_df['balance_difference'] != 0).sum()}")
        if (self.results_df['balance_difference'] != 0).any():
            print(f"Largest Positive Discrepancy: {self.results_df['balance_difference'].max():,.0f}")
            print(f"Largest Negative Discrepancy: {self.results_df['balance_difference'].min():,.0f}")
            print(f"Average Absolute Discrepancy: {self.results_df['balance_difference'].abs().mean():,.0f}")
        print("="*50)
    
    def run(self, output_filename=None):
        """Run the complete processing pipeline"""
        logger.info(f"Starting Season {self.season} processing...")
        
        # Load data
        self.load_data()
        
        # Process users
        self.process_users()
        
        # Add rankings and stats
        self.add_ranking_and_stats()
        
        logger.info("Processing complete!")
        
        return self.results_df


def main():
    """Main function to run the processor"""
    processor = Season2Processor()
    results = processor.run('staking_season_2_end.csv')
    return results


if __name__ == "__main__":
    results = main() 