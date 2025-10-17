# -*- coding: utf-8 -*-
"""
© 2025. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National 
Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of 
Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad 
National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. 
The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, 
irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute 
copies to the public, perform publicly and display publicly, and to permit others to do so.

@author: Aaron Pital (Los Alamos National Lab)
Created:  2024-04-19

Description:

"""

##################################################################################################
###    Spectra     ###############################################################################
##################################################################################################

import os
import numpy
import pandas
from tkinter import Tk, filedialog
from vamas import Vamas
import matplotlib.pyplot as plt

class Spectra:
    
    ''' v0.0.2   created:2024-04-19  modified:2024-09-06

    Class for handling spectra, including data cleaning from raw sources, inference from past
      examples, and other basic spectral analysis functions.
    
    INPUT:   lorem
    ACTION:  lorem
    OUTPUT:  lorem
    
    '''
    
    version = '0.0.2'
    date_modified = '2024-09-06'
    
    def __init__(self, data='', seam_path=''):
        
        #If data entry is provided, try and parse it
        if type(data) == list:
            #Go through data, check type, and try to open
            data_list = []
            type_list = []
            for this_item in data:
                if type(this_item) == numpy.ndarray:
                    data_list.append(this_item)
                    type_list.append(numpy.ndarray)
                elif type(this_item) == pandas.core.frame.DataFrame:
                    data_list.append(this_item)
                    type_list.append(pandas.core.frame.DataFrame)
                elif (type(this_item)== str) and (len(this_item)> 0):
                    if os.path.isfile(data):
                        # Add opening and parsing
                        output_dict = open_filename(data)
                        for sub_item, sub_type in zip(output_dict['data'], output_dict['types']):
                            data_list.append(sub_item)
                            type_list.append(sub_type)
                    else:
                        #TODO: if string not a filepath, try anLd parse it by context?
                        print()
                        print("Filepath not recognized if that was what you were going for:")
                        print(f"{data} not a valid filepath")
                        print()
                #if length of list entry is 0, just pass
                else:
                    pass

        elif type(data) == numpy.ndarray:
            self.data = [data]
            self.types = [numpy.ndarray]
        elif type(data) == pandas.core.frame.DataFrame:
            self.data = [data]
            self.types = [pandas.core.frame.DataFrame]
        elif (type(data)== str) and (len(data)> 0):
            if os.path.isfile(data):
                # Add opening and parsing
                output_dict = open_filename(data)
                self.data = output_dict['data']
                self.types = output_dict['types']
            else:
                print()
                print("Filepath not recognized if that was what you were going for:")
                print(f"{data} not a valid filepath")
                print()
                self.data = [] 
                self.types = []
        else:
            #Should only be default value at this point
            self.data = [] 
            self.types = []
            
            
            
    @staticmethod
    def open_filepath(filepath):
        output_dict = {
            'data':[],
            'types':[]
            }
        
        #Parse the filepath 
        
        return output_dict
    
    

class XPS:
    
    ''' v0.0.2   created:2024-04-19  modified:2024-09-06
    Wrapper class for static methods (currently; may change in future) related to parsing spectra.
    '''
    
    default_spot_dict = {
        'spot_size': 400,   #in microns
        'spot_profile': 'gaussian, broad'
        }
    
    load_option_dict = {
        'save_graphs':False,
        'save_spectra_as_single_csv': False,
        'save_spectra_as_individual_csvs': False,
        
        }
    
    @staticmethod
    def load(files='', mode='', option_dict = load_option_dict):

        if len(files) > 0:
            if type(files) == list:
                filenames = files
            elif type(files) == str:
                filenames = [files]
        else:
            root = Tk()
            filenames = filedialog.askopenfilenames()
            root.destroy()

        #Load each file and do stuff
        for filename in filenames:
            vamas_data = Vamas(filename)

            for item in vamas_data.blocks:
                
                spectrum_title = item.block_identifier
                y_values = item.corresponding_variables[0].y_values
                x_values = item.corresponding_variables[1].y_values
                char_energy = item.analysis_source_characteristic_energy
    
    
                x_start = item.x_start
                x_step = item.x_step
                x_stop = x_start + (x_step * (len(y_values)-1))
                x_values = numpy.linspace(x_start, x_stop, len(y_values))
                x_values = char_energy-x_values
                
                
                plt.scatter(x_values, y_values)
                plt.title(spectrum_title)
                plt.show()
                
                print(spectrum_title)
                print(f"{min(y_values)}:{max(y_values)}")
                print()
                print('______________')

        
        return 