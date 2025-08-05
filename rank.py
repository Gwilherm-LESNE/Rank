#%%
import re
import openelo
from difflib import SequenceMatcher
import numpy as np
import pandas as pd
import os
import datetime
import json

#%%

class Ranker:
    def __init__(self, method = 'elommr', previous_rank = None, cache_dir = './cache'):
        """
        Initialize the class

        Args:
            method (str, optional): type of rating algorithm to use. Defaults to 'elommr'.
            previous_rank (str, optional): Path to a previous rating file in csv format. Defaults to None.

        Raises:
            ValueError: _description_
        """

        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        if method == 'elommr':
            self.method = openelo.EloMMR()
            self.method_name = 'elommr'
        else:
            raise ValueError("Only 'elommr' as a method is handled yet")
        
        self.name_mapping = self.load_name_mappings()  # Load from cache
        self.players = {} # name -> Player object
        if len(self.name_mapping) > 0:
            self.players = {name: openelo.Player() for name in self.name_mapping.values()}
        self.race_history = []
        
        # Load confirmed different names cache
        self.different_names = self.load_different_names()

        # Load processed races cache only when using previous ranking
        self.processed_races = {}
        self.race_history = []
        if previous_rank:
            self.processed_races = self.load_processed_races()
            # Load race history cache for cyclist details
            self.race_history = self.load_race_history()

        if previous_rank:
            try:
                df = pd.read_csv(previous_rank)
                # Check if sigma column exists, otherwise use default
                if 'sigma' in df.columns:
                    self.previous_rank = dict(zip(df['name'].to_list(), df['rating'].to_list()))
                    self.previous_sigma = dict(zip(df['name'].to_list(), df['sigma'].to_list()))
                else:
                    # Backward compatibility: if no sigma column, use default sigma
                    self.previous_rank = dict(zip(df['name'].to_list(), df['rating'].to_list()))
                    self.previous_sigma = {name: 500.0 for name in df['name'].to_list()}
            except:
                self.previous_rank = None
                self.previous_sigma = None
        else: 
            self.previous_rank = None
            self.previous_sigma = None

        #Update a priori rank based on potential previous knowledge:
        if self.previous_rank:
            for name, rating in (self.previous_rank).items():
                name = self.get_or_create_player(name)
                sigma = self.previous_sigma.get(name, 500.0) if self.previous_sigma else 500.0
                self.players[name] = openelo.Player.with_rating(rating, sigma, update_time=0)


    def get_csv(self, path):
        """
        Opens a csv file based on its path

        Args:
            path (str): Path to the csv file

        Raises:
            KeyError: Raises Error if encoding is neither utf-8 nor utf-16

        Returns:
            pd.Dataframe: content of the csv file
        """
        try:
            out = pd.read_csv(path)
        except:
            try: 
                out = pd.read_csv(path, encoding='utf_16')
            except: 
                raise KeyError('encoding type provided to "read_csv" is not the right one')

        # Keep only the first 3 columns: place, name, club
        if len(out.columns) >= 3:
            out = out.iloc[:, [0, 1, 2]]
            out.columns = ['place', 'name', 'club']
            
            # Clean data
            out = out.dropna()
            out = out.reset_index(drop=True)

        return out


    def get_data(self, folder_path = './data/csv', ext = '.csv'):
        """
        Reads csv files in folder_path and returns pandas DataFrames

        Args:
            folder_path (str, optional): Path where to search for data files. 
                                        Only children files are taken into account. 
                                        Defaults to './data/csv'.
            ext (str, optional): Extension of the file to read (only csv handled yet). 
                                Defaults to 'csv'.

        Returns:
            list of pd.DataFrame: content of each file in a list
            list of datetimes: dates of the corresponding races (in format YYYY-MM-DD)
            list of str: file names of the processed races
        """
        df_list = []
        tmp_dates = []
        processed_files = []
        
        for file in sorted(os.listdir(folder_path)):
            if file in ['ranking.csv', 'rankings.csv']:
                continue
            file_path = os.path.join(folder_path,file)
            if os.path.isfile(file_path) and file.endswith(ext):
                # Skip files that have already been processed when using previous ranking
                if self.previous_rank and file in self.processed_races:
                    print(f"Skipping already processed file: {file}")
                    continue
                
                df_list.append(self.get_csv(file_path))

                processed_files.append(file)

                date_str = file.split('_')[0]
                try:
                    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    tmp_dates.append(date)
                except: 
                    tmp_dates.append(None)
                
        date_list = []
        for i, date in enumerate(tmp_dates):
            if date is None:
                date_list.append(min(tmp_dates))
            else:
                date_list.append(date)

        return df_list, date_list, processed_files


    def ask(self, n1,n2):
        """
        Interactive function which asks the user if two strings correspond to the same person or not

        Args:
            n1 (str): string for person1 id
            n2 (str): string for person2 id2

        Returns:
            bool: True if n1 and n2 correspond to the same person, False otherwise.
        """
        yes_choices = ['yes', 'y']
        no_choices = ['no', 'n']
        user_input = ''

        while not user_input.lower() in yes_choices+no_choices:
            user_input = input('Are %s and %s the same person? yes/no: '%(n1,n2))

        if user_input.lower() in yes_choices:
                return True
        elif user_input.lower() in no_choices:
                return False


    def normalize_name(self, name):
        """
        Normalize a runner's name to handle typos and variations
        """
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', name.lower().strip())
        
        # Replace accented letters with their non-accented counterparts
        accent_replacements = {
            'à': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ÿ': 'y',
            'ç': 'c',
            'ñ': 'n'
        }
        
        for accented, replacement in accent_replacements.items():
            normalized = normalized.replace(accented, replacement)
        
        # Remove special characters but keep letters, numbers, and spaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        return normalized
    

    def find_similar_name(self, name, threshold=0.85, threshold_2=0.93):
        """ 
        Find a similar name in existing runners to handle typos
        """
        normalized_name = self.normalize_name(name)
        
        # First check exact match
        if normalized_name in self.name_mapping:
            return self.name_mapping[normalized_name]
        
        # Check for similar names using sequence matching
        best_match = None
        best_score = 0
        
        for existing_name in self.players.keys():
            existing_normalized = self.normalize_name(existing_name)
            score = SequenceMatcher(None, normalized_name, existing_normalized).ratio()
            
            if score > best_score and score >= threshold:
                # Check if these names were previously confirmed as different
                name_pair = tuple(sorted([normalized_name, existing_normalized]))
                if name_pair in self.different_names:
                    continue  # Skip this pair as they were confirmed as different
                
                if score < threshold_2:
                    if self.ask(name, existing_name):
                        best_score = score
                        best_match = existing_name
                        self.name_mapping[normalized_name] = existing_name
                    else:
                        # Store that these names are different
                        self.different_names[name_pair] = True
                        self.save_different_names(self.different_names)
                else:
                    best_score = score
                    best_match = existing_name
        
        return best_match
    

    def get_or_create_player(self, name):
        """
        Get existing runner or create new one, handling typos
        """
        # Try to find similar name first
        similar_name = self.find_similar_name(name)
        
        if similar_name:
            return similar_name
        
        # Create new runner
        normalized_name = self.normalize_name(name)
        self.name_mapping[normalized_name] = name
        
        # Save updated name mappings to cache
        self.save_name_mappings(self.name_mapping)
        
        # Create a new Player
        self.players[name] = openelo.Player()
        return name


    def process_race(self, df, weight = 1.0, date = None, race_name = None):
        """Converts the DataFrame of one race into the standing format for openelo method

        Args:
            df (pd.DataFrame): DataFrame containing the standings of one race, with possible ties (Abandons)
            weight (float, optional): Weight for the race. Defaults to 1.0.
            date (int, optional): Date of the race. Defaults to None.
            race_name (str, optional): Name of the race file. Defaults to None.

        Returns:
            list: returns a list of [openelo.Player, int, int] where first and secondd ints are the place in standings. For ties, these are different.
        """

        df['name'] = df['name'].apply(self.get_or_create_player)

        standings = []
        last_place = 0
        for idx, row in df.iterrows(): 
            try: 
                place_1 = int(row['place']) - 1
                place_2 = place_1 
                last_place += 1
            except: 
                place_1 = last_place
                place_2 = len(df) - 1
            
            name = row['name']

            standings.append([self.players[name], place_1, place_2])

        # Update ratings using elommr
        crp = openelo.ContestRatingParams(weight=weight)
        if date:
            (self.method).round_update(crp, standings, contest_time=date)
        else:
            (self.method).round_update(crp, standings)
        
        # Store race history
        self.race_history.append({
            'race_data': df.copy(),
            'standings': standings,
            'race_name': race_name
        })


    def date_to_int(self,dt_time):
        return 10000*dt_time.year + 100*dt_time.month + dt_time.day


    def rank(self, folder, ext = 'csv'):
        """Computes the ranking based on the files contained in folder

        Args:
            folder (str): Path to where are stored the csv files with standings for each race
            ext (str, optional): extension file to read. Defaults to 'csv'.
        """
        df_list, date_list, processed_files = self.get_data(folder, ext)
        
        #For exponential weighting based on date
        differences = [d-min(date_list) for d in date_list]
        weights = [np.exp(-d/np.max(differences)) for d in differences]

        for idx,df in enumerate(df_list):
            if len(df) > 1:
                self.process_race(df, date=self.date_to_int(date_list[idx]), race_name=processed_files[idx]) #, weight=weights[idx]
            else:
                print(f"Skipping {df.to_string()}: not enough runners")
        
        # Save final name mappings to cache
        self.save_name_mappings(self.name_mapping)
        # Save final different names to cache
        self.save_different_names(self.different_names)
        # Save processed races cache
        # Update processed races cache with new files
        self.processed_races.update({file: 1 for file in processed_files})
        self.save_processed_races(self.processed_races)
        # Save race history cache
        self.save_race_history(self.race_history)


    def save_rankings(self, folder='./data/csv', fname='ranking', ext = 'csv'):
        """
        Save current ranking to CSV file
        """
        ranking = self.get_rankings()
        
        # Create DataFrame with name, rating, sigma, and races count
        df = pd.DataFrame(ranking, columns=['name', 'rating', 'sigma', 'races_participated'])
        df['rank'] = range(1, len(df) + 1)
        

        df = df[['rank', 'name', 'rating', 'sigma', 'races_participated']]
        
        # Ensure directory exists
        os.makedirs(folder, exist_ok=True)
        
        if ext == 'csv':
            fpath = os.path.join(folder,fname + '.csv')
            df.to_csv(fpath, index=False)
            print(f"Ranking saved to {fpath}")
        elif ext == 'html':
            fpath = os.path.join(folder,fname + '.html')
            df.to_html(fpath, index=False)
            print(f"Ranking saved to {fpath}")
        else:
            raise ValueError('File type other than "csv" or "html" are not handled')
        
        return df

    
    def get_rankings(self, top_n=None, min_races=3):
        """
        Get current Elo rankings sorted by rating, filtering out players with less than min_races
        
        Args:
            top_n (int, optional): Number of top players to return. Defaults to None.
            min_races (int, optional): Minimum number of races required. Defaults to 3.
        """
        # Get current ratings from players
        rankings = []
        for name, player in self.players.items():
            # Count races participated for this player
            races_participated = 0
            for race in self.race_history:
                race_data = race['race_data']
                if name in race_data['name'].values:
                    races_participated += 1
            
            # Only include players with at least min_races
            if races_participated >= min_races:
                rating = player.approx_posterior.mu
                sigma = player.approx_posterior.sig
                rankings.append((name, rating, sigma, races_participated))
        
        # Sort by rating (descending)
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        if top_n:
            rankings = rankings[:top_n]
        
        return rankings
    
    def get_player_stats(self, player_name):
        """
        Get statistics for a specific runner
        """
        if player_name not in self.players:
            return None
        
        player = self.players[player_name]
        stats = {
            'name': player_name,
            'current_rating': player.approx_posterior.mu,
            'rating_uncertainty': player.approx_posterior.sig,
            'races_participated': 0,
            'best_finish': float('inf'),
            'total_races': 0
        }
        
        for race in self.race_history:
            race_data = race['race_data']
            if player_name in race_data['name'].values:
                stats['races_participated'] += 1
                player_place = race_data[race_data['name'] == player_name]['place'].iloc[0]
                if isinstance(player_place, str) and (not player_place.isdigit()):
                    player_place = len(race_data)
                stats['best_finish'] = min(stats['best_finish'], int(player_place))
        
        if stats['best_finish'] == float('inf'):
            stats['best_finish'] = None
            
        return stats


    def print_top_rankings(self, top_n=20):
        """
        Print top N rankings
        """
        rankings = self.get_rankings(top_n)
        
        print(f"\nTop {len(rankings)} Runner Rankings:")
        print("-" * 70)
        print(f"{'Rank':<4} {'Name':<30} {'Elo Rating':<10} {'Races':<6}")
        print("-" * 70)
        
        for i, (name, rating, races) in enumerate(rankings, 1):
            print(f"{i:<4} {name:<30} {rating:<10.1f} {races:<6}")


    def save_name_mappings(self, name_mapping, cache_file='name_mappings.json'):
        """
        Save name mappings to cache file as JSON with alphabetically ordered keys
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        try:
            # Sort the dictionary by keys alphabetically
            sorted_mapping = dict(sorted(name_mapping.items()))
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_mapping, f, indent=2, ensure_ascii=False)
            print(f"Name mappings saved to cache: {cache_path}")
        except Exception as e:
            print(f"Error saving name mappings to cache: {e}")


    def load_name_mappings(self, cache_file='name_mappings.json'):
        """
        Load name mappings from cache file as JSON
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    name_mapping = json.load(f)
                print(f"Name mappings loaded from cache: {cache_path}")
                return name_mapping
            except Exception as e:
                print(f"Error loading name mappings from cache: {e}")
        return {}


    def save_different_names(self, different_names, cache_file='different_names.json'):
        """
        Save confirmed different names to cache file as JSON with first name as key and list of different names as value
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        try:
            # Convert tuple keys to single name key with list of different names
            converted_dict = {}
            for name_pair, _ in different_names.items():
                if isinstance(name_pair, tuple) and len(name_pair) == 2:
                    # Sort the names and use the first as key
                    sorted_names = sorted(name_pair)
                    key_name = sorted_names[0]
                    different_name = sorted_names[1]
                    
                    if key_name not in converted_dict:
                        converted_dict[key_name] = []
                    converted_dict[key_name].append(different_name)
            
            # Sort the dictionary by keys alphabetically
            sorted_different = dict(sorted(converted_dict.items()))
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_different, f)
            print(f"Different names saved to cache: {cache_path}")
        except Exception as e:
            print(f"Error saving different names to cache: {e}")


    def load_different_names(self, cache_file='different_names.json'):
        """
        Load confirmed different names from cache file as JSON and convert to internal tuple format
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    json_different_names = json.load(f)
                
                # Convert from JSON format (name -> list) back to internal format (tuple -> bool)
                different_names = {}
                for key_name, different_list in json_different_names.items():
                    for different_name in different_list:
                        # Create sorted tuple as key
                        name_pair = tuple(sorted([key_name, different_name]))
                        different_names[name_pair] = True
                
                print(f"Different names loaded from cache: {cache_path}")
                return different_names
            except Exception as e:
                print(f"Error loading different names from cache: {e}")
        return {}


    def save_processed_races(self, processed_races, cache_file='processed_races.json'):
        """
        Save processed race data to cache file as JSON
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(processed_races, f)
            os.makedirs('docs/cache', exist_ok=True)
            with open('docs/cache/processed_races.json', 'w', encoding='utf-8') as f:
                    json.dump(processed_races, f)
            print(f"Processed races saved to cache: {cache_path}")
        except Exception as e:
            print(f"Error saving processed races to cache: {e}")


    def load_processed_races(self, cache_file='processed_races.json'):
        """
        Load processed race data from cache file as JSON
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    processed_races = json.load(f)
                print(f"Processed races loaded from cache: {cache_path}")
                return processed_races
            except Exception as e:
                print(f"Error loading processed races from cache: {e}")
        return {}


    def save_race_history(self, race_history, cache_file='race_history.json'):
        """
        Save race history to cache file as JSON
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        try:
            # Convert race history to serializable format
            serializable_history = []
            for race in race_history:
                serializable_race = {
                    'race_data': race['race_data'].to_dict('records'),
                    'race_name': race.get('race_name', ''),
                    'standings': []  # We don't need to save standings as they're not used for display
                }
                serializable_history.append(serializable_race)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_history, f, indent=2, ensure_ascii=False)
            os.makedirs('docs/cache', exist_ok=True)
            with open('docs/cache/race_history.json', 'w', encoding='utf-8') as f:
                json.dump(serializable_history, f, indent=2, ensure_ascii=False)
            print(f"Race history saved to cache: {cache_path}")
        except Exception as e:
            print(f"Error saving race history to cache: {e}")


    def load_race_history(self, cache_file='race_history.json'):
        """
        Load race history from cache file as JSON
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    serializable_history = json.load(f)
                
                # Convert back to original format
                race_history = []
                for race in serializable_history:
                    race_data = pd.DataFrame(race['race_data'])
                    race_history.append({
                        'race_data': race_data,
                        'race_name': race.get('race_name', ''),
                        'standings': []  # Empty standings as they're not needed for display
                    })
                
                print(f"Race history loaded from cache: {cache_path}")
                return race_history
            except Exception as e:
                print(f"Error loading race history from cache: {e}")
        return []


    def clear_cache(self):
        """
        Clear the name mappings cache, different names cache, processed races cache, and race history cache
        """
        # Clear name mappings cache
        cache_path = os.path.join(self.cache_dir, 'name_mappings.json')
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                print(f"Name mappings cache cleared: {cache_path}")
            except Exception as e:
                print(f"Error clearing name mappings cache: {e}")
        
        # Clear different names cache
        different_cache_path = os.path.join(self.cache_dir, 'different_names.json')
        if os.path.exists(different_cache_path):
            try:
                os.remove(different_cache_path)
                print(f"Different names cache cleared: {different_cache_path}")
            except Exception as e:
                print(f"Error clearing different names cache: {e}")
        
        # Clear processed races cache
        processed_cache_path = os.path.join(self.cache_dir, 'processed_races.json')
        if os.path.exists(processed_cache_path):
            try:
                os.remove(processed_cache_path)
                print(f"Processed races cache cleared: {processed_cache_path}")
            except Exception as e:
                print(f"Error clearing processed races cache: {e}")
        
        # Clear race history cache
        history_cache_path = os.path.join(self.cache_dir, 'race_history.json')
        if os.path.exists(history_cache_path):
            try:
                os.remove(history_cache_path)
                print(f"Race history cache cleared: {history_cache_path}")
            except Exception as e:
                print(f"Error clearing race history cache: {e}")
        
        self.name_mapping = {}
        self.different_names = {}
        self.processed_races = {}
        self.race_history = []



#-----------------------------------------------------#



def main(csv_folder, output, top_n):
    """
    Main function to run the Elo ranking system
    """    
    
    # Initialize ranker
    ranker = Ranker()
    
    # Process all races
    ranker.rank(folder=csv_folder)
    
    # Display top rankings
    if top_n:
        ranker.print_top_rankings(top_n)
    
    # Save rankings to file
    filename, file_extension = os.path.splitext(output)
    ranker.save_rankings(folder=csv_folder, fname=filename, ext=file_extension) #For sabing and caching
    ranker.save_rankings(folder="docs/cache", fname=filename, ext=file_extension) #For plotting on the web
    
    print(f"\nElo ranking system completed !")
    print(f"Total runners: {len(ranker.players)}")
    print(f"Total races processed: {len(ranker.race_history)}")


def find_outlier(element, folder_path = './data/csv'):
    """
    Finds and prints every file in folder_path where element is present in the 'Name' column

    Args:
        element (str): string to search for in the files
        folder_path (str, optional): Folder where to scan the different files. Defaults to './CX'.
    """
    for file in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path,file)
        if os.path.isfile(file_path):
            csv = get_csv(file_path)
            if any([element in el for el in csv['name'].to_list()]):
                print(file_path)


# %%

if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='Calculate Elo rankings for runners')
    parser.add_argument('--csv_folder', type=str, default='data/csv', 
                       help='Folder containing CSV race files')
    parser.add_argument('--output', type=str, default='ranking.csv',
                       help='Output CSV file for rankings')
    parser.add_argument('--top_n', type=int, default=None,
                       help='Number of top rankings to display')
    
    args = parser.parse_args()
    
    main(args.csv_folder, args.output, args.top_n)
# %%
