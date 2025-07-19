# -*- coding: utf-8 -*-
"""
Created:  2024-04-12
Modified  2025-07-18
@author: Aaron Pital

Description: 

Changelog:
    - [2024-09-13] Renamed from 'SH2D' to 'SpatialArray' 
"""

import numpy
import pandas

class SpatialArray:
    ''' v0.1   Created:2024-09-24  Modified:2024-09-24
    Define a class to handle Spatially Hierarchical reference frame for 2D-ish samples and 2D-frameable data.
    '''
    
    version = '0.1.0'
    version_mod_date = '2024-09-24'
    default_spec_dict = {
        'array_type':'SH2D',  #'SH2D'  'SH3D'
        'sample_name':'Sample-1'
        }
    
    # Initialize class at a 'zero_scale_size' in meters
    def __init__(self, *sample_name, zero_size=0.333333):
        self.zero_size = zero_size
        self.level_sizes = self.make_level_sizes(zero_size)
        try:
            self.name = sample_name[0]
        except IndexError:
            self.name = sample_name
        self.level_edges()


class SH2D:
    
    ''' v0.1   Created:2024-03-07  Modified:2024-03-13
    Define a class to handle Spatially Hierarchical reference frame for 2D-ish samples and 2D-frameable data.
    '''
    
    version = '0.1.0'
    version_mod_date = '2024-09-15'
    minimum_size_threshhold = 1e-10    #smallest pixel scale in meters; typically 1e-10 == 1 angstrom
    
    
    # Initialize class at a 'zero_scale_size' in meters
    def __init__(self, zero_size=0.333333):
        
        self.zero_size = zero_size
        self.make_level_sizes(zero_size)
        

    
    # Generate 'S' sizes for each '0' level
    def make_level_sizes(self):
        
        #Initialize variables
        this_size = self.zero_size
        level = 1
        level_dict = {
           '0': self.zero_size 
           }
        
        # Return size levels (0 levels) and their associated 'S' sizes until a sub-angstrom size is reached.
        while this_size > 1e-10:
            this_size = this_size/3
            level_dict.update({str(level):this_size})
            level += 1
        
        self.level_sizes = level_dict

    
    # Take 'level_sizes' and generate 'level_edges' starting from top-left 0-0; dimensions in meters
    def pixeLSize_to_level(self):
        size_dict = self.level_sizes
        print(size_dict)
    
    
    ###############################################################################################################
    ###   Static functions   ######################################################################################
    ###############################################################################################################

    

    # Parse a SH2D location block and return a dictionary
    @staticmethod
    def location_block_parse(block):
        """ v0.0    created: 2024-09-01    modified: 2024-09-24
        Description
        """
        
        l_dict = {}
        
        #Split by ';' line-end 
        block_list = block.split(';')

        return l_dict

    
    # Given two arrays, produce an array for shared indices
    #   if more than one index 
    #   also produces a 'weight_array' for each entry in the 'index_array'
    @staticmethod
    def array_to_array_parse(block):
        """ v0.0    created: 2024-09-01    modified: 2024-09-24
        Description
        """
    
    
    
    
    
class Sample:
    
    ''' v0.1   Created:2024-09-10  Modified:2024-09-14
    Define a class to handle Spatially Hierarchical reference frame for 2D-ish samples 
    '''
    
    version = '0.1.0'
    version_mod_date = '2024-09-14'
    frame_blank = {
        'zero_size': 0.333333   # 1/3 of a meter
        }
    
    def __init__(self, name='', data= '', shape=[[]]):
        
        '''
        'shape'- Nx2 list of sample dimensions from edge-to-edge; by convention this list includes min & max dimensions;
                if 1x2, assume circle, if 2x2 assume rectangle if not identical, assume square if same, etc.  
        '''
        
        #Initialize variable
        self.data_flag = 'empty'
        self.data_incorp_dict = {
            'add_queue':{},
            'groups_added':{},
            'associations':{}
            }
        
        self.render_frames = {}
        
        #
        if len(name) > 0:
            self.sample_name = name
        else:
            self.sample_name = 'Sample-0'
        
        #
        #TODO: update with advanced data typing as project moves forward
        #    i.e. raw types (list, etc.) handled more efficiently because of project convention
        if len(data) > 0:
            if type(data) == dict:
                self.data_flag = 'dict'
                self.data= data
                
            elif type(data) == list:
                self.data_flag = 'list'
                self.data = data
                
            elif type(data) == numpy.ndarray:
                self.data_flag = 'numpy_array'
                self.data = data
            
            elif type(data) == pandas.core.frame.DataFrame:
                self.data_flag = 'pandas_dataframe'
                self.data = data
                
            elif type(data) == pandas.core.series.Series:
                self.data_flag = 'pandas_series'
                self.data = data                
    
    ###############################################################################################################
    ###   Static functions   ######################################################################################
    ###############################################################################################################
    
    
        