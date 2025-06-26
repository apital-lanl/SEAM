# -*- coding: utf-8 -*-
"""
Created on Aug 8 2024

@author: Aaron Pital
"""

from Recipe import Recipe

class Parsle:
    ''' v0.0.1   created:2024-07-27   modified:2024-08-10
    Custom parsing library to speed up complex activities. 
    
    '''
    
    version = '0.0.1'
    version_mod_date = '2024-08-10'

    parsle_dict = {
        "all": {},          #
        "bake": {},
        "dostart": {},      
        "each": {},
        "find": {},
        "field": {},
        "filepaths": {},
        "foreach": {},      #do something for 'foreach [list], dostart <instructions> dostops
        "iaw":{},           #"In Accordance With"- pull reference data and check specs
        "include": {},
        "load": {},
        "name": {},
        "named": {},        #assign a variable name
        "recipe": {},
        "run": {},
        "save": {},
        "store": {},
        "temp": {},
        }
    

    @staticmethod
    def read_parsle(text_block):
        ''' v0.1.0   created:2024-07-16   modified:2024-07-16
    
        Take a 'parsle' type block instruction and turn it into usable code.
        
        INPUT:   lorem 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''
        if type(text_block) == str:

            known_terms = list(Recipe.parsle_dict.keys())
            
            split_list = text_block.split(';')
            for line in split_list:
                line = line.replace(r'\n', '')  #Get rid of newline characters
                line = line.replace(r'\t', '')  #Get rid of tab characters
                entries = line.split(' ')
                for term in entries:
                    if term.lower() in known_terms:
                        pass
