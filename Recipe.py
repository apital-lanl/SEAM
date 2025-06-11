# -*- coding: utf-8 -*-
"""
Created on Apr 12 2024

@author: Aaron Pital
"""

##################################################################################################
###    Recipe      ###############################################################################
##################################################################################################
'''
TODO:
    - Add a 'recipe_index' check
    - Add a 'load_recipe' fucntion

'''

import importlib
import os

class Recipe():

    ''' v0.0.1   created:2024-04-12   modified:2024-08-10
    Description. 
    
    '''

    version = '0.0.1'
    version_mod_date = '2024-08-10'
    
    recipe_name_index = {
        0:  {0: "GenericTemplate_Recipe_0_0"},
        1:  {0: "CSVOpen_Recipe_1_0"},
        2:  {},
        3:  {},
        4:  {0: ""},
        5:  {},
        6:  {},
        7:  {},
        8:  {},
        9:  {0: "VK4OpenAndConvert_Recipe_9_0"},
        10: {},
        11: {},
        12: {},
        13: {},
        14: {},
        15: {},
        16: {},
        17: {},
        18: {},
        19: {},
        20: {0: "NumpyArrayOpen_Recipe_20_0"},
        21: {0: ""},
        22: {},
        23: {},
        }
    
    recipe_filepath_index = {
        "GenericTemplate_Recipe_0_0":       '',
        "CSVOpen_Recipe_1_0":               '',
        "VK4OpenAndConvert_Recipe_9_0":     '', 
        "NumpyArrayOpen_Recipe_20_0":       '',
        }
    
    recipe_file_dir = r".seam\Recipes"   #root\\recipe_file_dir 


    ##############################################################################################
    ###  Static methods/utilities   ##############################################################
    ##############################################################################################  


    @staticmethod
    def find_recipe_byid(recipe_id):
        ''' v0.1.0   created:2024-08-06   modified:2024-08-06
    
        Take a 
        
        INPUT:   lorem 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''
        
        #Try and pull the root directory from the Global
        try:
            target_directory = seam_root
        except:
            pass
        
    def recipe_lookup(primary_id, secondary_id):
        ''' v0.1.0   created:2024-08-21   modified:2024-08-21
        From IDs, check lookup dictionary and import that recipe 
        
        OUTPUT: name_string (str)- import string name for that recipe based on 'recipe_name_index'
        '''
        
        try:
            primary_id = int(primary_id)
            secondary_id = int(secondary_id)
            name_string = Recipe.recipe_name_index[primary_id][secondary_id]
        except:
            print("Failure of lookup; check ID numbers.")
            
        return name_string
        
    @staticmethod
    def recipe_summary(filename):
        
        ''' v0.1.0   created:2024-08-16   modified:2024-08-16
        Generate 
        '''
        
        #Simple parsing of filename
        module_name_guess = os.path.basename(filename).replace('.py', '')
        split_list = module_name_guess.split('_Recipe_')
        title = split_list[0]
        recipe_id = split_list[-1]
        recipe_list = recipe_id.split('_')
        recipe_flag_id = int(recipe_list[0])
        recipe_sub_id = [int(recipe_list[1])]
        
        if len(recipe_list) >2:
            for i in range(len(recipe_list)):
                recipe_sub_id.append(int(recipe_list[1+i]))
       
        #Create a return dictionary
        recipe_summary = {
            'recipe_title':title,
            'id_string':recipe_id,
            'flag_id':recipe_flag_id,
            'sub_ids':recipe_sub_id
            }
               
        #Import the Recipe file and populate summary keys if they exist
        my_module = importlib.import_module(module_name_guess)

        return recipe_summary
