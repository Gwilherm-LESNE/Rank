#%%
import openelo
from thefuzz import fuzz
import numpy as np
import pandas as pd
import os
import warnings
from datetime import datetime, timezone

#%%

def find_outlier(element, folder_path = './CX'):
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
            if any([element in el for el in csv['Name'].to_list()]):
                print(file_path)


class Ranker():
    def __init__(self, method = 'elommr', previous_rank = None):
        """
        Initialize the class

        Args:
            method (str, optional): type of rating algorithm to use. Defaults to 'elommr'.
            previous_rank (str, optional): Path to a previous rating file in csv format. Defaults to None.

        Raises:
            ValueError: _description_
        """

        if method == 'elommr':
            self.method = openelo.EloMMR()
            self.method_name = 'elommr'
        else:
            raise ValueError("Only 'elommr' as a method is handled yet")
        
        self.crp =  openelo.ContestRatingParams(weight=1.)

        self.players = None
        self.synonyms = None
        self.rank_history = None

        if not previous_rank is None:
            try:
                df = pd.read_csv(previous_rank, header=None, names=['Rank','Name','Rating'])
                self.previous_rank = dict(zip(df['Name'].to_list(),df['Rating'].to_list()))
            except:
                self.previous_rank = None
        else: 
            self.previous_rank = None


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
        #TODO: Read directly xlsx files and parse information from it
        try:
            out = pd.read_csv(path, header=None, names=['Place','Name'])
        except:
            try: 
                out = pd.read_csv(path, header=None, names=['Place','Name'], encoding='utf_16')
            except: 
                raise KeyError('encoding type provided to "read_csv" is not the right one')
        return out

   
    def get_data(self, folder_path = './CX', ext = 'csv'):
        """
        Reads csv files in folder_path and returns pandas DataFrames

        Args:
            folder_path (str, optional): Path where to search for data files. 
                                        Only children files are taken into account. 
                                        Defaults to './CX'.
            ext (str, optional): Extension of the file to read (only csv handled yet). 
                                Defaults to 'csv'.

        Returns:
            list of pd.DataFrame: content of each file in a list
            list of str: dates of the corresponding races (in format YYYY-MM-DD)
        """
        df_list = []
        date_list = []
        for file in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path,file)
            if os.path.isfile(file_path):
                if ext == 'csv':
                    df_list.append(self.get_csv(file_path))
                    date_list.append(file.split('_')[0])
        return df_list, date_list

    
    def ask(self, n1,n2):
        """
        Interactive function which asks the user if to strings correspond to the same person or not

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


    def update_syn(self, syn, n1, n2):
        """
        Updates the dictionnary of synonyms.

        Args:
            syn (dict): Dictionnary to update
            n1 (str): string synonym
            n2 (str): string synonym

        Returns:
            dict: Updated version of the dictionnary syn
        """
        target = n1
        if target in syn.keys():
            target = syn[target]

        source = n2
        if source in syn.keys():
            if syn[source]!=target:
                new_source = syn[source]
                syn[source] = target
                source = new_source
        syn[source] = target
        
        keys_list = [k for k, v in syn.items() if v == source]
        for key in keys_list:
            syn[key] = target
        return syn
    
    
    def filter_names(self, data):
        """Gets a DataFrame as input and outputs the list of the unique names in this DataFrame.
        Duplicates are handled by generating a dictionnary (synonyms) which contains the corresponding value for each key/entry.

        Args:
            data (DataFrame): DataFrame containing the names

        Returns:
            dict: dictionnary which value correspond to the synonym of the entry/key
            list: list of unique names, obtained after filtering duplicates/variants of the same names
        """
        names = []
        for df in data:
            names += df['Name'].to_list()
        names = sorted(list(set(names))) #get only unique names

        synonyms = {}
        for i,name in enumerate(names):
            for n in names[i+1:]:
                if 100>fuzz.ratio(n,name)>=93:
                    self.update_syn(synonyms,name,n)
                elif 93>fuzz.ratio(n,name)>=86:
                    if self.ask(name,n):
                        self.update_syn(synonyms,name,n)

        f_names = list(set(names)-set(synonyms.keys()))
        return synonyms, f_names
    
    
    def get_standing(self, df):
        """Converts the DataFrame of one race into the standing format for openelo method

        Args:
            df (pd.DataFrame): DataFrame containing the standings of one race, with possible ties (Abandons)

        Returns:
            list: returns a list of [openelo.Player, int, int] where first and secondd ints are the place in standings. For ties, these are different.
        """
        standing = []
        last_place = 1
        for idx in range(len(df)): 
            try: 
                place_1 = int(df['Place'][idx]) - 1
                place_2 = place_1 
                last_place += 1
            except: 
                place_1 = last_place
                place_2 = len(df)
            
            race_name = df['Name'][idx]
            if race_name in (self.synonyms).keys():
                name = self.synonyms[race_name]
            elif race_name in self.players:
                name = race_name
            else:
                warnings.warn('New racer detected !!! '+str(race_name)+' is not registered in the name database yet.')
                name = race_name
                for n in (self.players).keys():
                    if 100>fuzz.ratio(n,name)>=93:
                        self.update_syn(self.synonyms,name,n)
                    elif 93>fuzz.ratio(n,name)>=86:
                        if self.ask(name,n):
                            self.update_syn(self.synonyms,name,n)
                        else:
                            self.players[name] = openelo.Player()
                    else:
                        self.players[name] = openelo.Player() 

            standing.append([self.players[name], place_1, place_2])

        return standing


    def rank(self, folder, ext = 'csv'):
        """Computes the ranking based on the files contained in folder

        Args:
            folder (str): Path to where are stored the csv files with standings for each race
            ext (str, optional): extension file to read. Defaults to 'csv'.
        """
        df_list, dates = self.get_data(folder, ext)
        self.synonyms, names = self.filter_names(df_list) 
        self.players = {name:openelo.Player() for name in names}

        #Update a priori rank based on potential previous knowledge:
        if not self.previous_rank is None:
            for name,rating in (self.previous_rank).items():
                if name in (self.players).keys():
                    self.players[name] = openelo.Player.with_rating(rating, 500. ,update_time=0)
                elif name in (self.synonyms).keys():
                    self.players[self.synonyms[name]] = openelo.Player.with_rating(rating, 500. ,update_time=0)
                else:
                    for n in (self.players).keys():
                        if (100>fuzz.ratio(n,name)>=93) and (n in (self.players).keys()):
                            self.players[n] = openelo.Player.with_rating(rating, 500. ,update_time=0)
                        elif (93>fuzz.ratio(n,name)>=86) and (n in (self.players).keys()):
                            if self.ask(name,n):
                                self.players[n] = openelo.Player.with_rating(rating, 500. ,update_time=0)

        try:
            day = dates[0].split('-')
            first_date = datetime( int(day[0]), int(day[1]), int(day[2]))
        except:
            first_date = datetime(2022,12,22) #Put an old enough value so that it is before every race date

        for idx,df in enumerate(df_list):
            standing = self.get_standing(df)
            try:
                day = dates[idx].split('-')
                tmp_date = datetime( int(day[0]), int(day[1]), int(day[2]))
                contest_time = round((tmp_date-first_date).total_seconds())
            except:
                contest_time += (86400) #Corresponds to one day
            (self.method).round_update(self.crp, standing, contest_time=contest_time)
            
    
    def export_rank(self, save_name = None, ext = 'html'):
        """Creates a file with the ranking computed

        Args:
            save_name (str, optional): Name of the file to be saved. Defaults to None.
            ext (str, optional): File extension to take
        """
        if save_name is None:
            save_name = self.method_name

        ratings = [player.normal_factor.mu for player in (self.players).values()]
        names = list(self.players.keys())
        ratings, names =  zip(*sorted(zip(ratings,names), reverse=True))

        content = pd.DataFrame({'Rank': list(range(1,len(names)+1)),
                                'Name': names,
                                'Rating': ratings})
        
        fname = save_name + '_' + datetime.today().strftime('%Y-%m-%d')
        if ext == 'csv':
            content.to_csv(fname + '.csv', index=False)
        elif ext == 'html':
            content.to_html(fname + '.html', index=False)
        else:
            raise ValueError('File type other than "csv" or "html" are not handled')


# %%

if __name__ == '__main__':
    ranker = Ranker()
    ranker.rank(folder='./CX')
    ranker.export_rank()

# %%
