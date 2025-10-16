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

Created:  2024-08-08
Modified: 

@author: Aaron Pital (Los Alamos National Lab)

Description:

"""

from Recipe import Recipe


parsley_dict = {
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


class Parsley
    ''' v0.0.1   created:2024-07-27   modified:2024-08-10

    Custom parsing library to speed up complex activities for agent-based processing of data projects. 
    
    '''
    
    version = '0.0.1'
    version_mod_date = '2024-08-10'
    

    @staticmethod
    def read_parsley(text_block):
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
