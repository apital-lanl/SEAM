# -*- coding: utf-8 -*-
"""
Copyright 2025. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National 
Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of 
Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad 
National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. 
The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, 
irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute 
copies to the public, perform publicly and display publicly, and to permit others to do so.

Created:  2024-04-12
Modified: 

@author: Aaron Pital (Los Alamos National Lab)

Description:

"""

import os

class Fingerprint:
    
    ''' v0.0.2   created:2024-04-19  modified:2024-08-05

    Container  and object class for taking arbitrary filenames and parsing data 
    
    INPUT:   lorem
    ACTION:  lorem
    OUTPUT:  lorem
    
    '''
    
    version = '0.0.2'
    date_modified = '2024-10-26'
    hash_bin_data = {
        'version_summary':{
            'version': '0.0.1',
            'version_mod_date': '2024-10-26',
            'number_of_hash_bins': 0,
            },
        0:'file_flag_name',
        1:''
        }

    #Correlate a filetype with a flag, flag ID, and supplemental ID to find recipe for parsing that filetype    
    filetype_flags = {

        #unknown filetype
        '.unk':     {'flag_name':'UNK',     'flag_id': 0,   'recipe_supp_id': 0},
    
        #considered filetypes (varying degrees of support)
        '.bmp':     {'flag_name':'IMG',     'flag_id': 3,   'recipe_supp_id': 0},
        
        '.csv':     {'flag_name':'CSV',     'flag_id': 1,   'recipe_supp_id': 0},
        
        '.doc':     {'flag_name':'DOC',     'flag_id': 2,   'recipe_supp_id': 0},
        '.docx':    {'flag_name':'DOC',     'flag_id': 2,   'recipe_supp_id': 0},
        
        '.gif':     {'flag_name':'VID',     'flag_id': 12,  'recipe_supp_id': 0},
        
        '.jpeg':    {'flag_name':'IMG',     'flag_id': 3,   'recipe_supp_id': 0},
        '.jpg':     {'flag_name':'IMG',     'flag_id': 3,   'recipe_supp_id': 0},
        '.json':    {'flag_name':'IMG',     'flag_id': 15,  'recipe_supp_id': 0},

        '.mdi':     {'flag_name':'MDI',     'flag_id': 21,  'recipe_supp_id': 0},
        '.mpeg':    {'flag_name':'VID',     'flag_id': 12,  'recipe_supp_id': 0},
        '.mp4':     {'flag_name':'VID',     'flag_id': 12,  'recipe_supp_id': 0},
        
        '.npy':     {'flag_name':'NUMPY_ARRAY','flag_id': 20,'recipe_supp_id': 0},

        '.oim':     {'flag_name':'OIM',     'flag_id': 11,  'recipe_supp_id': 0},
        
        '.pdf':     {'flag_name':'PDF',     'flag_id': 4,   'recipe_supp_id': 0},
        '.png':     {'flag_name':'IMG',     'flag_id': 3,   'recipe_supp_id': 0},
        '.pnr':     {'flag_name':'PNR',     'flag_id': 5,   'recipe_supp_id': 0},
        
        '.spa':     {'flag_name':'SPA',     'flag_id': 6,   'recipe_supp_id': 0},
        '.spc':     {'flag_name':'SPC',     'flag_id': 18,   'recipe_supp_id': 0},
        '.spe':     {'flag_name':'SPE',     'flag_id': 7,   'recipe_supp_id': 0},

        '.tdms':    {'flag_name':'TDMS',     'flag_id': 22,   'recipe_supp_id': 0},
        '.tdms_index': {'flag_name':'TDMS_INDEX','flag_id': 23,'recipe_supp_id': 0},
        '.tif':     {'flag_name':'IMG',     'flag_id': 3,   'recipe_supp_id': 0},
        '.txt':     {'flag_name':'TXT',     'flag_id': 8,   'recipe_supp_id': 0},
        
        '.vk4':     {'flag_name':'KEYENCE', 'flag_id': 9,   'recipe_supp_id': 0},
        '.vk6':     {'flag_name':'KEYENCE', 'flag_id': 9,   'recipe_supp_id': 0},

        '.xlsx':    {'flag_name':'XLSX',    'flag_id': 10,  'recipe_supp_id': 0},

        #SEAM-specific formats
        '.grup' :   {'flag_name':'GROUP',  'flag_id': 13,  'recipe_supp_id': 0},
        '.metad':   {'flag_name':'META_DICT',  'flag_id': 16,  'recipe_supp_id': 0},
        '.prcs' :   {'flag_name':'PROCESS', 'flag_id': 19, 'recipe_supp_id': 0},
        '.seami':   {'flag_name':'SEAMi',  'flag_id': 17,  'recipe_supp_id': 0},
        '.specs':   {'flag_name':'SPECS',  'flag_id': 14,  'recipe_supp_id': 0},
        }
    
    #Generic 'type_names' to be used when making a .grup file
    grup_type_names = {
        'CSV':      [],
        'DOC':      [],
        'GROUP':    [],
        'IMG':      [],
        'KEYENCE':  [],
        'MDI':      [],
        'META_DICT':[],
        'MIXED':    [],
        'NUMPY_ARRAY':[],
        'OIM':      [],
        'PDF':      [],
        'PNR':      [],
        'PROCESS':  [],
        'SEAMi':    [],
        'SPA':      [],
        'SPC':      [],
        'SPE':      [],
        'SPECS':    [],
        'TDMS':     [],
        'TDMS_INDEX':[],
        'TXT':      [],
        'UNK':      [],
        'XLSX':     [],
        }
    
    #For template
    blank_type_names = {
        'CSV':      [],
        'DOC':      [],
        'GROUP':    [],
        'IMG':      [],
        'KEYENCE':  [],
        'MDI':      [],
        'META_DICT':[],
        'NUMPY_ARRAY':[],
        'OIM':      [],
        'PDF':      [],
        'PNR':      [],
        'PROCESS':  [],
        'SEAMi':    [],
        'SPA':      [],
        'SPC':      [],
        'SPE':      [],
        'SPECS':    [],
        'TDMS':     [],
        'TDMS_INDEX':[],
        'TXT':      [],
        'UNK':      [],
        'XLSX':     [],
        }


    ##############################################################################################
    ###  Static methods/utilities   ##############################################################
    ##############################################################################################  
    
    @staticmethod
    def get_basic_info(filepath):
        ''' v0.1.1   created:2024-04-19  modified:2024-08-12
        Description 
        
        INPUT:   lorem
        ACTION:  lorem
        OUTPUT:  lorem
        '''

        #get system data; 'time's are in seconds
        #   'accessed time' is last access; resolution 1 day?
        #   'unique fileindex' is system-dependent, but for same 'device id' it's unique to that file
        file_stats = os.stat(filepath)
        file_summary = {}
        file_summary.update ( {'filetype-permissions':file_stats.st_mode})
        file_summary.update ( {'device id':file_stats.st_dev})
        file_summary.update ( {'file owner id':file_stats.st_uid})
        file_summary.update ( {'unique fileindex':file_stats.st_ino})
        file_summary.update ( {'filesize':file_stats.st_size})
        file_summary.update ( {'accessed time':file_stats.st_atime})
        file_summary.update ( {'modified time':file_stats.st_mtime})
        file_summary.update ( {'created time':file_stats.st_ctime})
        
        #parse filepath to get some info
        file_dir = os.path.dirname(filepath)
        file_name = os.path.basename(filepath)
        split_list = file_name.split('.')
        
        #run through filename to get possible extensions
        extension_list = []
        for part in split_list:
            part = '.'+part
            try:
                ext = Fingerprint.filetype_flags[part]
                extension_list.append(part)
            except:
                pass
           #populate type information
        if len(extension_list)==1:
            file_summary.update ( {'filetype':extension_list[0]})
            #Try to lookup filetype info; if you can't find it, assign to UNK
            try:
                ext_dict = Fingerprint.filetype_flags[extension_list[0]]
                file_summary.update ( {'filetype flag':ext_dict['flag_name']})
                file_summary.update ( {'flag id':ext_dict['flag_id']})
                file_summary.update ( {'recipe supp id':ext_dict['recipe_supp_id']})
            except:
                file_summary.update ( {'filetype':'.unk'})
                ext_dict = Fingerprint.filetype_flags['.unk']
                file_summary.update ( {'filetype flag':ext_dict['flag_name']})
                file_summary.update ( {'flag id':ext_dict['flag_id']})
                file_summary.update ( {'recipe supp id':ext_dict['recipe_supp_id']})
        
        
        elif len(extension_list)>1:
            #add a sumplementary dictionary entry
            file_summary.update ( {'supp filetypes': {} })
            
            for idx in range(-1,-(len(extension_list)+1),-1):
                
                if idx==-1:
                    file_summary.update ( {'filetype':extension_list[idx]})
                    try:
                        ext_dict = Fingerprint.filetype_flags[extension_list[idx]]

                    except:
                        ext_dict = Fingerprint.filetype_flags['.unk']
                    file_summary.update ( {'filetype flag':ext_dict['flag_name']})
                    file_summary.update ( {'flag id':ext_dict['flag_id']})
                    file_summary.update ( {'recipe supp id':ext_dict['recipe_supp_id']})
                else:
                    new_dict = {}
                    new_dict.update ( {'filetype':extension_list[idx]})
                    try:
                        ext_dict = Fingerprint.filetype_flags[extension_list[idx]]
                    except:
                        ext_dict = Fingerprint.filetype_flags['.unk']
                    new_dict.update ( {'filetype flag':ext_dict['flag_name']})
                    new_dict.update ( {'flag id':ext_dict['flag_id']})
                    new_dict.update ( {'recipe supp id':ext_dict['recipe_supp_id']})
                    file_summary['supp filetypes'].update ( {idx:new_dict})
        
        elif len(extension_list)==0:
            file_summary.update ( {'filetype':'.unk'})
            ext_dict = Fingerprint.filetype_flags['.unk']
            file_summary.update ( {'filetype flag':ext_dict['flag_name']})
            file_summary.update ( {'flag id':ext_dict['flag_id']})
            file_summary.update ( {'recipe supp id':ext_dict['recipe_supp_id']})
                        
        #TODO: add filetype-related summary additions
        
        return file_summary
    
    
    @staticmethod
    def get_advanced_info(filepath, input_dict={}):
        ''' v0.0.1     created:2024-08-14     modified:2024-08-14
        Get fancy info from outside functional analysis, either from Recipes or 
          some other code specification source.
        '''
        #Initialize variables 
        output_dict = {}
        
        return
    
    
    

