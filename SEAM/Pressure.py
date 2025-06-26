# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 15:23:18 2024

@author: Aaron Pital (LANL)

Library for handling pressure data. 

"""

#Used imports
import pandas as pd
from tkinter import filedialog, Tk
from operator import itemgetter
import os
from tqdm import tqdm
import numpy as np
from numpy import linspace
import matplotlib.pyplot as plt
from datetime import datetime

#Prior import list
from scipy.optimize import curve_fit
from scipy.stats import linregress

import matplotlib.pyplot as plt
from matplotlib import cm

import winsound
from operator import itemgetter

##################################################################################################
###    Variables   ###############################################################################
##################################################################################################

gas_properties_dict = {
    'Xx': {
        'long_name': 'Gas',
        'nominal_mass': 0,
        'isotopic_ratios':{
            
            },
        'speed_of_sound': 0,
        'VdW_A': 0,
        'VdW_B': 0,        
        },
    
    }


blank_gas_species_entry = {
    'gas': 100,
    }

##################################################################################################
###    Classes     ###############################################################################
##################################################################################################


class Parapress:
    
    ''' v0.1.3   created:2024-10-16   modified:2024-11-07
    
    Wrapper class for handling XLSX outputs from Jeff Wheat's ParaPress program (Visual Basic 8).
    MKS baratrons are read by analog-to-digital converters into VB8 program.
    Output is (CHANNEL #)-MMDDYYY-TTTTTT XLSX file with columns:
               Date     Time        Reading
                        (HH:MM:SS)  (torr)
    '''
    
    version = '0.1.2'
    date_modified = '2024-11-06'
    
    # def __init__(self, channel_directory='', filename_lists = [[]]):
    #     '''
    #     Initialize an object for a set of files
    #     '''
    #     # Get files if none specified
    #     if len(filename_lists)==1 and len(filename_lists[0])<1:
    #         #if empty, start list of lists
    #         self.filenames = [select_files()]
    #     else:
    #         self.filenames = filename_lists
        
    #     #Initialize the data-container (Pandas DataFrame)
    #     self.data = pd.DataFrame([])
        
    #     #Combine files if more than one selected
    #     for file_list in self.filenames:
    #         comb_df = Parapress.combine(file_list, df= self.data)
    #         #explicitly set .data to new DataFrame
    #         self.data = comb_df
            
    
    
    # def add_filenames(self, files = [[]], name=''):
    #     # Get files if none specified
    #     self.filenames = self.filenames.append(select_files())
        
        
    # def add_dir_by_channel(self, directory = ''):
        
    #     if len(directory) <1:
    #         this_root = Tk()
    #         directory = filedialog.askdirectory("Select directory with Channel data")
    #         this_root.destroy()
            
    #     #Walk the directory and get sub-directories or 
    
    ##############################################################################################
    ###    Static  methods   #####################################################################
    ##############################################################################################
    
    @staticmethod
    def select_files(channels = [], start_date = '', end_date =''):
        ''' v1.1   created:2024-10-16   modified:2024-11-07
        Get files from a dialog box selection. If start or end date are specified, only pull days within that period.
        Only display CSV or XLSX files for selection.
        Date/time format = 'YEAR-MONTH-DAY-HRMINSEC'
        channel data format = 19-08212024-160139  (CH-MMDDYYY-HHMMSS)
        '''
        
        blank_channel_entry = {
            'start_date': '',
            'end_date': '',
            'filenames': [],
            'display_names': [],
            'missing_data':{}
            }
        
        #Open dialogbox to select file directory
        root = Tk()
        filenames = filedialog.askopenfilenames(filetypes = [("Excel Files", "*.xlsx; *.csv")])
        root.destroy()
        
        #Wrap up files into a dictionary split out by channel
        filenames = Parapress.select_files_bydate(filenames, start_date= start_date, end_date= end_date)
        filenames_dict = Parapress.dict_from_filenames(filenames, channels = channels)
        
        return filenames_dict
    
    
    @staticmethod
    def select_from_dir(channels=[], start_date = '', end_date =''):
        ''' v1.1   created:2024-10-16   modified:2024-11-07
        Get files from a dialog box selection. If start or end date are specified, only pull days within that period.
        Only display CSV or XLSX files for selection.
        Date/time format = 'YEAR-MONTH-DAY-HRMINSEC'
        channel data format = 19-08212024-160139  (CH-MMDDYYY-HHMMSS)
        '''
        
        #Open dialogbox to select file directory
        root = Tk()
        walk_dir = filedialog.askdirectory()
        root.destroy()
        
        filenames = []
        #Walk directory and select all Parapress output files (based on filename alone)
        for dirpath, directories, files in os.walk(walk_dir):
            for filename in files:
                #Separate statements in case filetypes are handled differently in the future
                if filename.endswith(".xlsx"):
                    filename = filename.replace('.xlsx', '')
                    filename_split = filename.split('-')
                    date_check = len(filename_split[1])== 8
                    time_check = len(filename_split[2])== 6
                    
                    if date_check and time_check:
                        filenames.append(os.path.join(dirpath, filename))
                    
                if filename.endswith(".csv"):
                    filename = filename.replace('.csv', '')
                    filename_split = filename.split('-')
                    date_check = len(filename_split[1])== 8
                    time_check = len(filename_split[2])== 6
                    
                    if date_check and time_check:
                        filenames.append(os.path.join(dirpath, filename))
                        
        #Wrap up files into a dictionary split out by channel
        filenames = Parapress.select_files_bydate(filenames, start_date= start_date, end_date= end_date)
        filenames_dict = Parapress.dict_from_filenames(filenames, channels = channels)
        
        return filenames_dict

    
    @staticmethod
    def filenames_to_dataframe(filenames_dict, plot_block = True, datetime_coerce = 'latest',
                               main_directory = ''):
        ''' v2.0   created:2024-11-06   modified:2025-06-16
        Adapted from previous Jupyter Notebook code.
        datetime_coerce = 'latest', 'earliest'
        '''

        # List out the actual filenames for each date's file
        df_list = []
        #    Make a single list of lists of every file in the directory
        
        walk_name_part = os.walk(main_directory)   
        for ch_index, ch_dir in tqdm(enumerate(channel_dirs)):
            print('__________________________________________________________________________________________________')
            print("Working on channel ", os.path.basename(ch_dir))
            print()
            frame_list = []
            name = os.path.basename(ch_dir)
            #   date_select.value   name_set
            for date_index, date_time in enumerate(date_select.value):
                print()
                print("Date Index: ", date_index)
                print("Date-Time: ", date_time)
                print()
                filename = os.path.join(ch_dir, name+'-'+date_time) #'date_time' is common between the channels, so just add the channel name to get the filename
                try:
                    this_frame = pd.read_csv(filename, parse_dates=[['Date', 'Time']])
                    new_name = name+'-Reading'
                    this_frame = this_frame.rename(columns={' Reading': new_name, ' Time': 'Time'})
                      #Delete the midnight entries because they're 0's
                    midnight_index = this_frame[this_frame[new_name]==0].index
                    this_frame = this_frame.drop(midnight_index).reset_index(drop=True)
                    try:
                        this_frame['Date_Time'] = pd.to_datetime(this_frame['Date_ Time'])  #Fix for deprecated time handling
                    except:
                        this_frame['Date_Time'] = this_frame['Date_Time'].replace('nan nan', 'nan')
                        this_frame['Date_Time'] = this_frame['Date_Time'].dropna()
                        this_frame['Date_Time'] = pd.to_datetime(this_frame['Date_Time'])
                      #If this is the first date entry, get the first date_time
                    if date_index == 0:
                        this_frame= this_frame.sort_values(by='Date_Time')
                        first_datettime = this_frame['Date_Time'][0]
                        this_frame['Diff'] = this_frame['Date_Time']-first_datettime
                        this_frame['Time-seconds'] = this_frame['Diff'].dt.total_seconds()
                        this_frame['Time-seconds'] = this_frame[this_frame['Time-seconds'].notnull()]['Time-seconds']
                        this_frame['Time-seconds'] = this_frame['Time-seconds'].round().astype(int)
                        this_frame['Time-minutes']= this_frame['Time-seconds']/60
                        this_frame['Time-minutes'] = this_frame['Time-minutes'].round().astype(int)
                    else:
                        this_frame['Diff'] = this_frame['Date_Time']- first_datettime
                        this_frame['Time-seconds']= this_frame['Diff'].dt.total_seconds()
                        this_frame['Time-seconds'] = this_frame[this_frame['Time-seconds'].notnull()]['Time-seconds']
                        this_frame['Time-seconds'] = this_frame['Time-seconds'].round().astype(int)
                        this_frame['Time-minutes']= this_frame['Time-seconds']/60
                        this_frame['Time-minutes'] = this_frame['Time-minutes'].round().astype(int)
                    frame_list.append(this_frame[['Date_Time', 'Time-minutes', new_name]])
                    
                except FileNotFoundError:
                    print("File error on:")
                    print(filename)
                    print("Attempting to find correct date with any time start.")
                    
                    date = date_time.split('-')[0]
                    # Walk the directory to find a file with the correct date
                    for root, dirs, files in os.walk(ch_dir):
                        for file in files:
                            if date in file:
                                new_name = file
                    
                    # Open that file instead 
                    filename = os.path.join(ch_dir, new_name) #'date_time' is common between the channels, so just add the channel name to get the filename
                    try:
                        this_frame = pd.read_csv(filename, parse_dates=[['Date', 'Time']])
                        #print(this_frame.head())
                        new_name = name+'-Reading'
                        this_frame = this_frame.rename(columns={' Reading': new_name, ' Time': 'Time'})
                        #Delete the midnight entries because they're 0's
                        midnight_index = this_frame[this_frame[new_name]==0].index
                        this_frame = this_frame.drop(midnight_index).reset_index(drop=True)
                        if date_index == 0:
                            this_frame= this_frame.sort_values(by='Date_Time')
                            first_datettime = this_frame['Date_Time'][0]
                            this_frame['Diff'] = this_frame['Date_Time']-first_datettime
                            this_frame['Time-seconds']= this_frame['Diff'].dt.total_seconds()
                            this_frame['Time-seconds'] = this_frame['Time-seconds'].round().astype(int)
                            this_frame['Time-minutes']= this_frame['Time-seconds']/60
                            this_frame['Time-minutes'] = this_frame['Time-minutes'].round().astype(int)
                        else:
                            this_frame['Diff'] = this_frame['Date_Time']-first_datettime
                            this_frame['Time-seconds']= this_frame['Diff'].dt.total_seconds()
                            this_frame['Time-seconds'] = this_frame['Time-seconds'].round().astype(int)
                            this_frame['Time-minutes']= this_frame['Time-seconds']/60
                            this_frame['Time-minutes'] = this_frame['Time-minutes'].round().astype(int)
                        frame_list.append(this_frame[['Date_Time', 'Time-minutes', new_name]])

                    except FileNotFoundError:
                        print("File is still not reading:")
                        print(filename)
                
                except KeyError:
                    # Some corrupted time/pressure files are not parsed correctly
                    # In that case, just skip adding anything to the files to concatenate
                    pass

            try:
                this_df = pd.concat(frame_list, axis=0)
                df_list.append(this_df)
            except:
                print("Value Error")
                
        # Find a common datetime and coerce temperature to 'earliest' or 'latest'
        first_datetime_list = []
        for i in range(0,len(df_list)):
            df_list[i] = df_list[i].sort_values(by='Date_Time').reset_index(drop=True)
            this_first_datetime = df_list[i]['Date_Time'][0]
            first_datetime_list.append(this_first_datetime)
           
           #Coerce datetimes for temperature channels (often start at midnight while experiments start after lunch)
        if datetime_coerce == 'earliest':
            comparison_time = min(first_datetime_list)
        if datetime_coerce == 'latest':
            comparison_time = max(first_datetime_list)
        for i in range(0,len(df_list)):
                this_df = df_list[i]
                these_columns = this_df.columns
                for column in these_columns:
                    if '21' in column or '22' in column:
                        df_list[i]['Time-seconds'] = (df_list[i]['Date_Time']-comparison_time)
                        df_list[i]['Time-seconds'] = df_list[i]['Time-seconds'].dt.total_seconds().round().astype(int)
                        df_list[i]['Time-minutes'] = df_list[i]['Time-seconds']/60
                        df_list[i]['Time-minutes'] = df_list[i]['Time-minutes'].round().astype(int)
                
        # Combine all the DataFrames
        df = pd.DataFrame(df_list[0])
        for i in range(1,len(df_list)):
            df = df.merge(df_list[i], on = 'Time-minutes', how = 'outer', suffixes = [f'_{i+1}', f'_{i+2}'])
            
        # Grab only the useful columns from above
        # TODO: can make use of other columns?
        clean_columns = []
        for column in df.columns:
            if 'reading' in column.lower() or 'time-' in column.lower():
                clean_columns.append(column)
        clean_df = df[clean_columns]

        clean_df.dropna(how='any')

        # Plot the results
        plt.figure(figsize=(10, 7))
        if plot_block:
            
            # It's assumed the last column is the temperature data, and it's plotted with each file
            color_list = ['midnightblue', \
                          'blue', \
                          'cornflowerblue', \
                          'steelblue', \
                          'lightseagreen', \
                          'mediumaquamarine', \
                          'mediumspringgreen']

            color_list = ['lightpink', \
                          'darkorange', \
                          'darkorchid', \
                          'crimson', \
                          'black', \
                          'dodgerblue', \
                          'lightgreen', \
                         'slategrey', \
                         'crimson', \
                         'black', \
                         'orange',]

            # Plot all columns or a selection of columns
            columns = clean_df.columns
            #columns = ['17-Reading', '18-Reading', '19-Reading', '20-Reading', '21-Reading'] 

            legend_list = []
            for index, column in enumerate(columns):
                # Don't plot "index" or "{time}" column
                if ('index' not in column) and ('Time' not in column):
                    color_idx = len(legend_list)
                    legend_list.append(column)

                    # Take only a given columns data with the time column and drop "nan" valued rows
                    this_df = clean_df[['Time-minutes', column]].dropna(axis=0)

                    # Do the actual plotting; df.plot() has some nice features, but is finicky
                    #plt.plot(this_df['Time-seconds'], this_df[column], color = color_list[color_idx], linewidth = 5)
                      #Workaround for "Multi-dimensional indexing (e.g. `obj[:, None]`) is no longer supported..."
                      #Not sure if this ever needs to be reverted to the form above
                      #TODO: figure out at some point if I need to fix this
                    plt.scatter(this_df['Time-minutes'].values, this_df[column].values, color = color_list[color_idx], linewidth = 5)
                      #Finicky DataFrame plotting native to Pandas; probably useful at some point in the future
                    #df.plot(x='seconds', y=[column, df.columns[-1]])

            plt.legend(legend_list)
            plt.xlabel('Time (min)')
            #plt.xlabel('Date')
            plt.ylabel('Pressure/Temp. (Torr/C)')

            plt.show()
        
        return clean_df
    
    
    def process(self, data_df, graph=False, gas_species_dict ={}):
        pass

        
    ###    Utilities   ###########################################################################
        
        
    @staticmethod
    def dict_from_filenames(filenames, channels=[]):
        ''' v1.1   created:2024-11-06   modified:2025-06-16
        Sort ParaPress outout filenames by date and return sorted list.
        Option for only selecting some channels.
        Output
        '''
        
        blank_channel_entry = {
            'start_date': '',
            'end_date': '',
            'filenames': [],
            'display_names': [],
            'missing_data':{}
            }
        
        #Initialize variables
        filenames_dict = {}
        filename_tuples = {}
        if len(channels) < 1:
            channels = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]
        for channel in channels:
            filenames_dict.update({channel: blank_channel_entry})
            filename_tuples.update({channel: []})
            
        for filename in filenames:
            
            end_split_filename = os.path.basename(filename).split('.')
            if len(end_split_filename) == 2:
                clean_filename = end_split_filename[0]
            elif len(end_split_filename) >2:
                clean_filename= end_split_filename[0]
                for part in end_split_filename[1:-2]:
                    clean_filename = clean_filename + '_' + part
            else:
                clean_filename = end_split_filename
                
            if type(clean_filename)== list:
                clean_filename = clean_filename[0]
            
            try:
                split_list = clean_filename.split('-')
                this_channel = int(split_list[0])
                
                this_year = int(split_list[1][4:8])
                this_month = int(split_list[1][0:2])
                this_day = int(split_list[1][2:4])
                
                this_hour = int(split_list[2][0:2])
                this_minute = int(split_list[2][2:4])
                this_second = int(split_list[2][4:6])
                comb_time = int(split_list[2])
                
                filename_tuples[channel].append((filename, this_year, this_month, this_day, comb_time))
            except:
                print()
                print(f"Parse error on:")
                print(f"\t {clean_filename}")
        
        #Iteratively sort a list from seconds
        for channel in channels:
            for idx in [4,3,2,1]:
                filename_tuples[channel] = sorted(filename_tuples[channel], key = itemgetter(idx), reverse = False)
            filenames_list = [part[0] for part in filename_tuples[channel]]
            display_names = [str(name[1])+'-'+str(name[2])+'-'+str(name[3])+':'+str(name[4]) for name in filename_tuples[channel]]
        
            filenames_dict[channel]['filenames'] = filenames_list
            filenames_dict[channel]['display_names'] = display_names
        
        return filenames_dict
        
        
    @staticmethod
    def select_files_bydate(filenames, start_date='', end_date=''):
        ''' v1.0   created:2024-11-06   modified:2024-11-06
        For a list of filenames, return a list of filenames that fall within specified dates.
        '''
        #Check date formats and parse 
        if len(start_date) > 0:
            split_list = start_date.split('-')
            start_year = int(split_list[0])
            start_month = int(split_list[1])
            start_day = int(split_list[2])
            
            try:
                start_time = split_list[3]
            except IndexError:
                start_time = 000000
            
            if len(str(start_time)) == 6:
                start_hr = int(start_time[0:2])
                start_min = int(start_time[2:4])
                start_sec = int(start_time[4:6])
            else:
                print("Unclear time bounds; defaulting to latest time.")
                start_hr = 00
                start_min = 00
                start_sec = 00
        else:
            start_year = 1940
            start_month = 1
            start_day = 1
            start_hr = 1
            start_min = 1
            start_sec = 1
            start_date = str(start_year) + '-' + str(start_month) + '-' + str(start_day) + \
                             '-' + str(start_hr) + str(start_min) + str(start_sec)
            
        if len(str(end_date)) > 0:
            split_list = end_date.split('-')
            end_year = int(split_list[0])
            end_month = int(split_list[1])
            end_day = int(split_list[2])
            
            try:
                end_time = split_list[3]
            except IndexError:
                end_time = 000000
            
            if len(end_time) == 6:
                end_hr = int(start_time[0:2])
                end_min = int(start_time[2:4])
                end_sec = int(start_time[4:6])
            else:
                print("Unclear time bounds; defaulting to latest time.")
                end_hr = 00
                end_min = 00
                end_sec = 00
        else:
            end_year = 3000
            end_month = 12
            end_day = 31
            end_hr = 23
            end_min = 59
            end_sec = 59
            end_date = str(end_year) + '-' + str(end_month) + '-' + str(end_day) + \
                             '-' + str(end_hr) + str(end_min) + str(end_sec)
                
        end_datetime = datetime(end_year, end_month, end_day, \
                                hour= end_hr, minute=end_min, second=end_sec)
        start_datetime = datetime(start_year, start_month, start_day, \
                                hour= start_hr, minute=start_min, second=start_sec)
        
        filtered_filenames = []
        for filename in filenames:
            
            #Get rid of filename extension; prob smarter ways to do this, but this makes it customizable
            end_split_filename = os.path.basename(filename).split('.')
            if len(end_split_filename) == 2:
                clean_filename = end_split_filename[0]
            elif len(end_split_filename) >2:
                clean_filename= end_split_filename[0]
                for part in end_split_filename[1:-2]:
                    clean_filename = clean_filename + '_' + part
            else:
                clean_filename = end_split_filename
                
            #Fix filetype issue and flattern list to string
            if type(clean_filename) == list:
                clean_filename = clean_filename[0]
            
            #
            try:
                split_list = clean_filename.split('-')
                this_channel = int(split_list[0])
                
                this_year = int(split_list[1][4:8])
                this_month = int(split_list[1][0:2])
                this_day = int(split_list[1][2:4])
                
                this_hour = int(split_list[2][0:2])
                this_minute = int(split_list[2][2:4])
                this_second = int(split_list[2][4:6])
                
                this_datetime = datetime(this_year, this_month, this_day, \
                                        hour= this_hour, minute=this_minute, second=this_second)
                    
                if (this_datetime>=start_datetime) and (this_datetime<=end_datetime):
                    filtered_filenames.append(filename)
            except:
                print()
                print(f"Parse error on:")
                print(f"\t {clean_filename}")
                
        return filtered_filenames
        
    
##############################################################################################
###    Utility class   #######################################################################
##############################################################################################

class Utilities:
    
    ''' v0.1.0   created:2024-10-16   modified:2024-10-17
    Custom utilites for Pressure classes, but which also are useful for uses outside these Classes.
    '''
    
    version = '1.0'
    date_modified = '2024-10-17'

    @staticmethod
    def process(input_data):
        
        if by_date:
            pass
        
        #TODO: allow for other sorting methods
        else:
            pass
        
        pass
    
    
    