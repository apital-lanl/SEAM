# -*- coding: utf-8 -*-
"""
Created on Aug 10 2024

@author: Aaron Pital
"""

import json
import os
from pathlib import Path
from tkinter import Tk, filedialog

from TypeHash import Fingerprint

#TODO: alter to handle filename clash better
#   - Add 'clash' key to 'meta_dict'
#   - Get rid of full filepath key in 'meta_dict_lookup'


class Meta:
    
    ''' v0.1.2     created 2024-08-10     modified: 2024-09-10
    
    Utility class for handling 'meta_dict' files. 'meta_dict' files store summary stats
      for individual files and act as a repository/pointer-dict for processes that involve
      those files. 
    
    '''
    version = '0.1.2'
    version_mod_date = '2024-09-10'
    
    @staticmethod
    def meta_index_lookup(filepath, meta_dict_index={}, seam_root = '', update_dict={}):
        
        ''' v0.1.1     created 2024-08-10     modified: 2024-08-16
        Update a meta_dict_index with location of 'meta_dict' for a file. If none foound, make what's needed.
        'meta_dict_index'- dictionary of basename or basename hash to filepath of meta_dict; if not specified, try and find it. If it can't be found, make a temp.
        '''
        
        #Split filepath into directory and filename
        this_directory = os.path.dirname(filepath)
        this_directory_head = os.path.basename(this_directory)
        this_filename = os.path.basename(filepath)
        status = {
            'directory_path': this_directory,
            'directory_head': this_directory_head,
            'filename': this_filename,
            'index':'',
            'meta_dict':'',
            'meta_dict_index_filepath':''
            }
        
        #Check for '.seam' directory in the root
        if len(seam_root)>0:
            meta_dict_root = os.path.join(seam_root, r'meta_dicts')
        else:
            try:
                root_home = str(Path.home())
                meta_dict_root = os.path.join(root_home, r'.seam\meta_dicts')
            except:
                #seam_obj = SEAM()
                #meta_dict_root = seam_obj.metadict_root_directory
                #TODO: Circular import from Meta-SEAM-Meta; just make a new file if the above fails
                meta_dict_root = os.path.join(root_home, r'.seam\meta_dicts')
        
        #Look for the index where it should be and assign the 'right' path to the output status dict
        index_path_guess = os.path.join(meta_dict_root, 'meta_dict_index.json')
        status['meta_dict_index_filepath']= index_path_guess  #final version of 'meta_dict_index' will be dumped here; assigned each time because it's just easier that way (and cheap probably)
        
        #If no 'meta_dict_index' supplied, try and find it, a temporary one, or start a new temporary one.
        if len(meta_dict_index) == 0:
            
            #Check for 'meta_dict_index.json' in 'meta_dict_root'
            if os.path.isfile(index_path_guess):
                index_filepath = index_path_guess
                with open(index_filepath, 'r') as file:
                    meta_dict_index = json.load(file)
                status['index'] = 'loaded, full'
            
            elif os.path.isfile(os.path.join(meta_dict_root, 'temp_meta_dict_index.json')):
                index_filepath = os.path.join(meta_dict_root, 'temp_meta_dict_index.json')
                with open(os.path.join(meta_dict_root, 'temp_meta_dict_index.json'), 'r') as file:
                    meta_dict_index = json.load(file)
                status['index'] = 'loaded, temp'
                
            else:
                index_filepath = os.path.join(meta_dict_root, 'temp_meta_dict_index.json')
                meta_dict_index = {}
                status['index'] = 'new, temp'
                
        filename_str = f"{this_filename}.metad"
        meta_dict_filepath = os.path.join(meta_dict_root, filename_str)

        try:
            #Check if filename is in index; if not, raises KeyError and moves to 'except'
            #   If key exists in index, then check if file actually exists and make a new 'meta_dict' if not
            return_filepath = meta_dict_index[this_filename]
            
            #Check if the 'meta_dict' file actually exists like the index says it should
            if not os.path.isfile(return_filepath):
                meta_dict_index, dict_status = Meta.update_meta_dict(filepath, meta_dict_root, meta_dict_index)
                status['meta_dict'] = 'replacement'
            else:
                status['meta_dict'] = 'existing'

        except:
            meta_dict_index.update( {this_filename: meta_dict_filepath} )
            meta_dict_index, dict_status = Meta.update_meta_dict(filepath, meta_dict_root, meta_dict_index)
            status['meta_dict'] = 'new'
            status['index'] = 'updated'
            
        #No matter, if update isn't empty, update the meta_dict
        if len(update_dict) > 0:
            meta_dict_index, dict_status = Meta.update_meta_dict(filepath, meta_dict_root, meta_dict_index, update_dict = update_dict)
        
        return meta_dict_index, status
                
            
    @staticmethod
    def update_meta_dict(original_filepath, meta_dict_root, meta_dict_index, update_dict={}):
        ''' v0.1.0     created 2024-08-10     modified: 2024-08-10
        'meta_dict_index'- dictionary of basename or basename hash to filepath of meta_dict; if not specified, try and find it. If it can't be found, make a temp.
        '''
        
        this_directory = os.path.dirname(original_filepath)
        this_filename = os.path.basename(original_filepath)
        file_directories_list = Meta.list_directories_recursive(original_filepath)
        key_directory = file_directories_list[0]
        
        meta_filename_str = f"{this_filename}.metad"
        meta_filepath = os.path.join(meta_dict_root, meta_filename_str)
        
        #Get basic file info
        basic_file_summary = Fingerprint.get_basic_info(original_filepath)
        
        #TODO: use TypeHash to get advanced file summary based on recipes
          #TODO: put into PROCESS queue 
        
        #Create blank entry for this file
        blank = {
            'original_directory_path':this_directory,
            'original_directory_list': file_directories_list,
            'original_filename':this_filename,
            'metad_filepath': meta_filepath,
            'clash_merges':[],
            'basic_file_summary': basic_file_summary,
            'associated_prcs_files':[],
            'associated_grup_files':[],
            'associated_seami_files':[],
            'associated_specs_files':[],
            'associated_events':[],
            'associated_recipes':[],
            }
        
        #Assign blank entry to immediate first (lowest) directory name above filename
        this_entry = {
            key_directory: blank
            }
        #TODO: use status better; 
        status = {
            'load_recipe':'',
            'queue_proposed':False,
            }
        
        #TODO: TypeHash lookup filetype, Recipe lookup blank info, load into SEAM 'Proposed' queue
        
        if os.path.isfile(meta_filepath):
            #Open meta_dict 
            try:
                with open(meta_filepath, 'r') as file:
                    old_meta_dict = json.load(file)
            except:
                print(f"Fail import on filepath: \n {meta_filepath}")
                
            #Test if this directory has been entered before
            those_dir_keys = list(old_meta_dict.keys())
            if key_directory in those_dir_keys:
                if len(update_dict) >0:
                    old_meta_dict[key_directory].update(update_dict)
                    with open(meta_filepath, 'w') as file:
                        json.dump(old_meta_dict, file, indent=4)
            else:
                old_meta_dict.update(this_entry)
                old_meta_dict[key_directory].update(update_dict)
                with open(meta_filepath, 'w') as file:
                    json.dump(old_meta_dict, file, indent=4)
            
        else:
            new_meta_dict = this_entry
            new_meta_dict[key_directory].update(update_dict)
            #Try to save to root .seam folder.
            try:
                with open(meta_filepath, 'w') as file:
                    json.dump(new_meta_dict, file, indent=4)
            #If no root .seam defined, save to local repo by 'seam_config.json' data
            except:
                #Find config file if main root doesn't exist
                dump_dir = os.path.join(seam_config.working_directory, 'meta_dicts')
                trial_filepath = os.path.join(dump_dir, meta_filename_str)
                
                with open(trial_filepath, 'w') as file:
                    json.dump(new_meta_dict, file, indent=4)
            
    
        #Update 'meta_dict_index'
          #If filename is already in index, add full filepath to 'clash' dict and use that as the index
        try:
            test_entry = meta_dict_index[this_filename]
          #If filename is new, use filename as key
        except:
            meta_dict_index.update( {this_filename : meta_filepath} )
        
        return meta_dict_index, status
    
    
    @staticmethod
    def list_directories_recursive(full_filepath):
        ''' v0.1.0     created 2024-08-12     modified: 2024-08-12
        '''
       
        #Assign filepath to new variable in case you want the filepath in future versions
        new_path = os.path.dirname(full_filepath)
        
        #Initalize variables
        length_difference = 20
        last_length = 1000
        directories_list = []
        while length_difference >0:
            base_name = os.path.basename(new_path)
            new_path = os.path.dirname(new_path)
            length_difference = last_length - len(new_path)
            last_length = len(new_path)
            if length_difference >0:
                directories_list.append(base_name)
            else:
                directories_list.append(new_path)
            
        return directories_list
    
    
    @staticmethod
    def defuzz_meta_entries(meta_dict):
        ''' v0.0.1     created 2024-08-12     modified: 2024-08-12
        'meta_dict'- dictionary with at least one key
        
        Process a meta_dict to de-fuzz entries for filenames that should actually be identical.
        Smart merging of "directory1//filename" & "directory2//filename" when directories are equivalent.
        '''
        
        dict_keys = list(meta_dict.keys())
        defuzzed_meta_dict = {}
        
        if len(dict_keys) > 1:
            # Do simple comparison of directory names (information theoretic match)
            
            
            # If unsure (or settings require), flag for manual curation as a .prcs file
            
            pass
        
        
        return defuzzed_meta_dict
    
    @staticmethod
    def walk_directory(filepath='', seam_root=''):
        
        ''' v0.1.0     created 2024-08-16     modified: 2024-08-16
        
        Process a meta_dict to de-fuzz entries for filenames that should actually be identical.
        Smart merging of "directory1//filename" & "directory2//filename" when directories are equivalent.
        '''
        
        #Get directory if none defined
        if len(filepath) == 0:
            root = Tk()
            directory = filedialog.askdirectory()
            root.destroy()
        else:
            directory = filepath
    

        #Initialize dump flag
        index_write_flag = False
        update_count = 0
        
        grup_filepaths = []
        prcs_filepaths = []
        specs_filepaths= []
        seami_filepaths = []
        #Do the walkin
        for root, dirs, files in os.walk(directory):
            for file in files:
                this_filepath = os.path.join(root, file)
                
                #While walking, look for SEAM filetypes
                main_filetype = file.split('.')[-1].lower()
                if main_filetype == ".grup":
                    grup_filepaths.append(os.path.join(root, file))
                if main_filetype == ".prcs":
                    prcs_filepaths.append(os.path.join(root, file))
                if main_filetype == ".specs":
                    specs_filepaths.append(os.path.join(root, file))
                if main_filetype == ".seami":
                    seami_filepaths.append(os.path.join(root, file))
                
                #Lookup the file and return index, etc. 
                try:
                    meta_dict_index, status = Meta.meta_index_lookup(this_filepath, meta_dict_index, seam_root= seam_root)
                except:
                    meta_dict_index, status = Meta.meta_index_lookup(this_filepath, seam_root= seam_root)
                
                #If a new index has been created or updated, flag that for dumping down below
                if status['index'] == 'updated':
                    index_write_flag = True
                    meta_dict_filepath = status['meta_dict_index_filepath']
                    update_count += 1
                    
        #Dump 'meta_dict_index' as a JSON if it's been changed/created
        if index_write_flag:
            with open(meta_dict_filepath, 'w') as filepath:
                json.dump(meta_dict_index, filepath, indent=4)
        
        #Tell everyone what you've done
        output_dict = {
            'new_meta_dict_indices':update_count,
            'meta_dict_index_filepath':meta_dict_filepath,
            'grup_filepaths': grup_filepaths,
            'prcs_filepaths': prcs_filepaths,
            'specs_filepaths': specs_filepaths,
            'seami_filepaths': seami_filepaths,
            }
                
        print(f"Finished with {update_count} updates to 'meta_dict_index'")
        
        return output_dict

    
    
class Summary:
    
    ''' v0.0.0     created 202-     modified: 202-
    
    Description
    
    '''
    version = '0.0.0'
    version_mod_date = '202-'
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    