#%%
import os
import shutil
import camelot
import pandas as pd
pd.options.mode.chained_assignment = None

print('parse_files.py imports: Done')
#%%

class FileParser:
    def __init__(self, read_folder, write_folder = 'data/csv'):
        self.read_folder = read_folder
        self.files = os.listdir(read_folder)
        self.write_folder = write_folder
        shutil.rmtree(write_folder) 
        os.makedirs(write_folder)

    def clean_dataframe(self, df):
        indices = []
        for idx, row in df.iterrows():
            place = row.to_list()[0].replace(" ", "")
            if (not place.isdigit()) and (place != "Ab."):
                indices.append(idx)
        
        df.drop(indices, inplace=True)
        df = df.reset_index(drop=True)
        ### DROP CADET/JUNIOR/MINIMES/POUSSINS/etc.
        cate_to_keep = ['E','S','V','SV','A','SA','F/E','F/S','F/V','F/SV','F/A','F/SA'] #['1', '2', '2obs.', '3', '4']
        drop = True
        for idx, row in df.iterrows():
            category = row.to_list()[3].replace(" ", "")
            if category in cate_to_keep:
                drop = False
                break
        if drop:
            indices = list(range(len(df)))
            df.drop(indices, inplace=True)
        
        return df 
    
    def parse_file(self, file_path):
        tables = camelot.read_pdf(file_path, pages='1-end', suppress_stdout=True)
        results = []
        for idx, table in enumerate(tables):
            columns = [0,1,2,3]
            df = table.df.iloc[:,columns] # only keep the first four columns (Place, Name, Club and Age Category)
            df = self.clean_dataframe(df)
            if len(df) > 0:
                first_place = df.iloc[0, 0] #Check if the first place of the df is 1
                if first_place == '1':
                    results.append(df)
                else:
                    results[-1] = pd.concat([results[-1], df])
        return results

    def parse_files(self):
        for file in self.files:
            results = self.parse_file(os.path.join(self.read_folder, file))
            for idx, result in enumerate(results):
                result.to_csv(os.path.join(self.write_folder, f'{file.split(".")[0]}_{idx}.csv'), index=False, header=['place', 'name', 'club', 'category'])
        return None

print('parse_files.py classes & functions: Done')
# %%

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--read_folder', type=str, default='data/pdf', help='Folder to read the pdf files from')
    parser.add_argument('--write_folder', type=str, default='data/csv', help='Folder to write the csv files to')
    args = parser.parse_args()

    print('Parsing files...', end='')
    file_parser = FileParser(args.read_folder, args.write_folder)
    file_parser.parse_files()
    print(' Done !')