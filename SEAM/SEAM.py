# -*- coding: utf-8 -*-
"""
Created on Apr 12 2024

@author: Aaron Pital
"""

##################################################################################################
###    SEAM      #################################################################################
##################################################################################################
  
import json
from tkinter import Tk, filedialog
from pathlib import Path
import os
import shutil
import errno
  
  #import other SEAM modules
from TypeHash import TypeHash
from Meta import Meta


   #    SEAM variables   ##########################################################################
   
   
   
class SEAM:
    
    ''' v0.0.4   created:2024-04-12   modified:2024-09-10
    
    Open a SEAM meta object. If no directory is supplied, assume reliance on prior data.
    If a directory is supplied and data has never been processed previously, start new 'logging' files and 
        begin populating them with meta info about data in the folder. If directory has been processed previously, 
        try updating 
    '''
    
    version = '0.0.4'
    date_modified = '2024-09-10'

    
    def __init__(self, work_dir='', alt_root=''):
        
        global seam_root, current_seam_oject

        #initialize some object instance fields
        self.log = {
            'errors':{
                },
            'activity':{
                },
            
            }
        self.queued_processes = {
            }
        
        self.failed_processes = {
            }
        
        #set flags for SEAM repositories
        recipe_check = False
        meta_check = False

        # Check for SEAM root folder and get global
        root_home = str(Path.home())
        if len(alt_root)>0:
            self.user_root = alt_root
        else:
            self.user_root = root_home
        self.current_workingdir = root_home
        #reset 'root_home'
        root_home = self.user_root
        
        # .seam root directory and branch
        if len(work_dir)>0:
            self.current_workingdir = work_dir
        
          #no matter what, try to find the root SEAM repo; make one in the root if you can't find it there
        trial_dirs = []
        for root, dirs, files in os.walk(self.user_root, topdown=False):
           for name in dirs:
               if '.seam' in name.lower():
                  trial_dirs.append(os.path.join(root, name))
        
          #alternate directory '.seam' search method; not sure how it's getting to directories outside root          
        #for item in os.listdir(self.user_root):
        #    if os.path.isfile(os.path.join(self.user_root, '.seam')):
        #        trial_dirs.append(os.path.join(self.user_root, '.seam'))

        if len(trial_dirs) == 1:
            
            seam_guess = trial_dirs[0]
            
            #Just check that two of the required directorie exist and assume all else is groovy
            meta_check = os.path.isdir(os.path.join(seam_guess, "meta_dicts"))
            typehash_check = os.path.isdir(os.path.join(seam_guess, "meta_dicts"))
            
            if meta_check and typehash_check:
                self.seam_root = seam_guess
                seam_root = os.path.join(root_home, ".seam") #set the global 'seam_root' as well
            else:
                self.create_seam_directory(os.path.join(root_home, ".seam"))
        
        elif len(trial_dirs) == 0:
            folder_check = os.path.isdir(os.path.join(root_home, ".seam"))
            if not folder_check:
                self.create_seam_directory(os.path.join(root_home, ".seam"))
                
           #If META or REC filetypes are found, parse into dictionary
    
           #Otherwise start a dictionary and save a placeholder (i.e. blank) META and REC file
              #Look in SEAM root file 
              
              
        #set the global 'seam_root' to the
        seam_root = os.path.join(root_home, ".seam")
        self.seam_root = seam_root

    
    def create_seam_directory(self, root_dir, ok_exist_mode = False):
        
        ''' v0.1.1   created:2024-06-19   modified:2024-06-19
        
        Generate the SEAM backend repository structure.
        
        '''

        #Generate directories
        os.makedirs(root_dir, exist_ok = ok_exist_mode)
                    
        self.metadict_root_directory = os.path.join(root_dir, "meta_dicts")
        os.makedirs(self.metadict_root_directory, exist_ok = ok_exist_mode)
        
        self.recipes_root_directory = os.path.join(root_dir, "Recipes")
        os.makedirs(self.recipes_root_directory, exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Group Events"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Objects"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Processes"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Environments"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Filetypes"), exist_ok = ok_exist_mode)
        
        os.makedirs(os.path.join(self.recipes_root_directory, "Perspectives"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Perspectives", "Samples"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Perspectives", "Projects"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.recipes_root_directory, "Perspectives", "Timelines"), exist_ok = ok_exist_mode)
        
        self.typehash_root_directory = os.path.join(root_dir, "TypeHashes")
        os.makedirs(self.typehash_root_directory, exist_ok = ok_exist_mode)

        self.event_root_directory = os.path.join(root_dir, "Events")
        os.makedirs(self.event_root_directory, exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.event_root_directory, "Proposed"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(self.event_root_directory, "History"), exist_ok = ok_exist_mode)

        self.event_root_directory = os.path.join(root_dir, "Data")
        os.makedirs(self.event_root_directory, exist_ok = ok_exist_mode)

        self.template_root_directory = os.path.join(root_dir, "Templates")
        os.makedirs(self.template_root_directory, exist_ok = ok_exist_mode)
        
        self.log_root_directory = os.path.join(root_dir, "logs")
        os.makedirs(self.log_root_directory, exist_ok = ok_exist_mode)

        #Create generic config file 
        config_dict = {
            'primary_root': root_dir,
            'secondary_roots':[],
            'log_folder': self.log_root_directory
            }
        
        config_filepath = os.path.join(root_dir, 'seam_config.json')
        
        with open(config_filepath, 'w', encoding='utf-8') as file:
            json.dump(config_dict, file, ensure_ascii=False, indent=4)
    
    
    def load(self, filename, input_dict = {}, *args):
        ''' v0.0.0   created:2024-07-09   modified:2024-07-09
        Load data for a .prcs or .seami file into a SEAM object.
        '''

        filetype_dict = TypeHash.filetype_flags
        
        if len(args)>0:
            seam_files = []
            spec_files = []
            meta_dict_files = []
            directories = []
            for arg in args:
                pass
            
            
    def do(self, input_dict = {}):
        
        ''' v0.1.0   created:2024-08-21   modified:2024-08-22
        Walk a directory and identify what processing is required; 
        '''
        
        pass
    
    
    def mirror_root_repository(self, new_directory, overwrite_permission = False):
        ''' v0.1.0   created:2024-06-20   modified:2024-06-20
        
        Make a direct copy of .seam root repository to a new location. If 
        
        INPUT:   lorem
                (optional)
                'overwrite_permission'- if False, raises 'file exists error' when same files/directories are encountered.
                                        Otherwise, if True, WILL OVERWRITE the source directory. 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''

        if not os.path.isdir(os.path.join(new_directory, ".seam")):
            new_filepath = os.path.join(new_directory, ".seam")
        else:
            new_filepath = new_directory

        try:
            shutil.copytree(self.root_directory, new_filepath, dirs_exist_ok = overwrite_permission)
        except OSError as exc: 
            if exc.errno in (errno.ENOTDIR, errno.EINVAL):
                shutil.copy(self.root_directory, new_filepath)
            else: raise
        
        print()
        print("Creating mirror repository to:")
        print(f"\t {new_filepath}")
        print()


    def process_directory(self, directory, seam_root = '', force_reprocess = False):
        ''' v0.1.0   created:2024-06-20   modified:2024-06-20
    
        Walk a directory and identify what processing is required; 
        
        '''

        #Walk the directory and make sure each file has a 'meta_dict'; reasonably fast if the directory is < ~1 Gb
        metawalk_output_dict = Meta.walk_directory(filepath= directory, seam_root= seam_root)
        
        
    
    ##############################################################################################
    ###  Static methods/utilities   ##############################################################
    ##############################################################################################    
    
    @staticmethod
    def create_seami_file(new_filename = '', open_filename_dialog= True):
        ''' v0.1.0   created:2024-07-11   modified:2024-07-11 
    
        Make a direct copy of .seam root repository to a new location. If 
        
        INPUT:   lorem 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''
        pass
    
    
    @staticmethod
    def find_seami_files(directory):
        ''' v0.1.0   created:2024-08-22   modified:2024-08-22
        Description        
        '''
        trial_files = []
        for root, dirs, files in os.walk(directory, topdown=False):
           for filename in files:
               if '.seami' in filename.lower():
                  trial_files.append(os.path.join(root, filename))
                  
    
    @staticmethod
    def interim_process_dump(dump_dict, dump_filepath= '', seam_root = ''):
        ''' v0.1.1   created:2024-08-26   modified:2024-09-10
        Temporarily dump a dictionary as a JSON rather than incorporate fully into a SEAMi file (or equivalent)
        '''
        if len(dump_filepath)>0:
            dump_filepath = SEAM.Utilities.checkfile(dump_filepath)
        
        else:
            # Check for SEAM root folder and get global
            root_home = str(Path.home())
            if len(seam_root)>0:
                user_root = seam_root
            else:
                user_root = root_home
            #reset 'root_home'
            root_home = user_root
           
              #no matter what, try to find the root SEAM repo; make one in the root if you can't find it there
            trial_dirs = []
            for root, dirs, files in os.walk(user_root, topdown=False):
               for name in dirs:
                   if '.seam' in name.lower():
                      trial_dirs.append(os.path.join(root, name))
    
            if len(trial_dirs) == 1:
                seam_guess = trial_dirs[0]
                
                #Just check that two of the required directorie exist and assume all else is groovy
                meta_check = os.path.isdir(os.path.join(seam_guess, "meta_dicts"))
                typehash_check = os.path.isdir(os.path.join(seam_guess, "TypeHashes"))
                
                if meta_check and typehash_check:
                    seam_root = seam_guess
                else:
                    Utilities.create_temp_seam_directory(root_home)
            
            dump_dir = os.path.join(seam_root, 'logs')
            trial_filepath = os.path.join(dump_dir, 'MaunualInterimProcessFile')
            trial_filepath = trial_filepath + ".json"
            dump_filepath = Utilities.checkfile(trial_filepath)
            
        #Try dumping to main root .seam repo, but dump to local repo as a backup 
        try:
            with open(dump_filepath, 'w') as file:
                json.dump(dump_dict, file, indent=4)
        except FileNotFoundError:
            #TODO: Fix this to dump to a root temp directory; no idea what 'seam_config' was supposed to be
            # #Find config file if main root doesn't exist
            # import seam_config
            # dump_dir = os.path.join(seam_config.working_directory, 'logs')
            # trial_filepath = os.path.join(dump_dir, 'MaunualInterimProcessFile')
            # trial_filepath = trial_filepath+".json"
            # dump_filepath = Utilities.checkfile(trial_filepath)
            
            # with open(dump_filepath, 'w') as file:
            #     json.dump(dump_dict, file, indent=4)
        

    def func_temp():
            ''' v0.1.0   created:2024-   modified:2024-
        
            Description
            
            INPUT:   lorem 
            ACTION:  lorem
            OUTPUT:  lorem
            
            '''
            pass
    
    
    
    
class Group:
    ''' v0.0.1   created:2024-08-12   modified:2024-08-12
    Utility class for parsing, creating, and maintaining .grup (GROUP) files
    '''
    
    version = '0.1.0'
    date_modified = '2024-09-02'
    
    blank_grup_dict = {
     'template_summary':{
         'version': '0.1.0',
         'date_modified': '2024-08-20',
         },
     
     'name':'',
     'type_name':'',
     
     'date_created': '',
     'time_created': '',
     'directory_path': '',
     'bottom_directory': '',
     'common_filename': '',
      
     'included_files': [],
     'excluded_files': [],
     'associations': {
         'seami':[],
         'prcs':[],
         'grup':[],
         'meta_d':[],
         'sample':[],
         'timeline':[],
         'process':[]
         
         }
     
     }
    
    
    @staticmethod
    def load(grup_filepath):
        ''' v0.1.0   created:2024-   modified:2024-
        Description        
        '''
        
        pass
    
    @staticmethod
    def find(directory):
        ''' v0.1.0   created:2024-08-22   modified:2024-08-22
        Description        
        '''
        trial_files = []
        for root, dirs, files in os.walk(directory, topdown=False):
           for filename in files:
               split_name = filename.split('.')
               if '.grup' in split_name[-1].lower():
                  trial_files.append(os.path.join(root, filename))


    @staticmethod
    def make(directory = '', filenames=[]):
        ''' v0.1.0   created:2024-09-01   modified:2024-09-01
        Make a .grup file for a set of filenames; if filenames not specified, open dialog box to select them.        
        '''
        
        #Initialize variables
        status = ''
        
        #if filenames specified, bundle them; otherwise ask for file list
        if len(filenames)>0:
            pass
        else:
            #Open to directory (if specified) and ask for filenames to be bundled
            if len(directory) == 0:
                root = Tk()
                filenames = filedialog.askopenfilenames(hometitle= "Select files to wrap into a .grup file")
                root.destroy()
            else:
                root = Tk()
                filenames = filedialog.askopenfilenames(initialdir= directory,  hometitle= "Select files to wrap into a .grup file")
                root.destroy()
            
        #Parse filenames to get TypeHash results for proposed actions
        filetype_flags = []
        for file in filenames:
            #Get file ending and append to list if new
            this_end = os.path.basename(file).split('.')[-1].lower()
            if this_end not in filetype_flags:
                filetype_flags.append(this_end)
        
        #If only one filetype is included, lookup in TypeHash class and guess at a process to run
        
        return status
            
        

class Process:
    ''' v0.0.1   created:2024-08-14   modified:2024-08-20
    Utility class for parsing, creating, and maintaining .prcs (PROCESS) files
    '''
    
    blank_process = {
        'name': '',
        'version': '',
        'date_created': '',
        'date_modified': '',
        'recipe_filename':'',
        'specs_filename':'', 
        
        }
    
    
    @staticmethod
    def find(directory):
        ''' v0.1.0   created:2024-08-22   modified:2024-08-22
        Description        
        '''
        trial_files = []
        for root, dirs, files in os.walk(directory, topdown=False):
           for filename in files:
               split_name = filename.split('.')
               if '.prcs' in split_name[-1].lower():
                  trial_files.append(os.path.join(root, filename))
    
    
    @staticmethod
    def process():
        ''' v0.1.0   created:2024-   modified:2024-
    
        Description
        
        INPUT:   lorem 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''
        
        pass
    
    
    @staticmethod
    def func_temp():
        ''' v0.1.0   created:2024-   modified:2024-
    
        Description
        
        INPUT:   lorem 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''
        pass
    
    
    
class Specs:
    ''' v0.0.1   created:2024-08-14   modified:2024-08-14
    Utility class for parsing, creating, and maintaining .specs (SPECIFICATIONS) files
    '''
    
    @staticmethod
    def find(directory):
        ''' v0.1.0   created:2024-08-22   modified:2024-08-22
        Description        
        '''
        trial_files = []
        for root, dirs, files in os.walk(directory, topdown=False):
           for filename in files:
               split_name = filename.split('.')
               if '.specs' in split_name[-1].lower():
                  trial_files.append(os.path.join(root, filename))
    
    
    @staticmethod
    def func_temp():
        ''' v0.1.0   created:2024-   modified:2024-
    
        Description
        
        INPUT:   lorem 
        ACTION:  lorem
        OUTPUT:  lorem
        
        '''
        pass
    
    
    
class Utilities:
    ''' v0.0.1   created:2024-08-14   modified:2024-10-18
    Utility class for parsing, creating, and maintaining .specs (SPECIFICATIONS) files
    '''
    
    @staticmethod
    def checkfile(path):
        """
        Taken verbatim from:
        https://stackoverflow.com/questions/29682971/auto-increment-file-name-python
        """
        path      = os.path.expanduser(path)
        
        if not os.path.exists(path):
           return path
        
        root, ext = os.path.splitext(os.path.expanduser(path))
        dir       = os.path.dirname(root)
        fname     = os.path.basename(root)
        candidate = fname+ext
        index     = 0
        ls        = set(os.listdir(dir))
        while candidate in ls:
                candidate = "{}_{}{}".format(fname,index,ext)
                index    += 1
        return os.path.join(dir,candidate)
    
    @staticmethod
    def create_temp_seam_directory(root_dir, ok_exist_mode = False):
        
        ''' v0.1.1   created:2024-06-19   modified:2024-06-19
        
        Generate the SEAM backend repository structure.
        
        '''
        new_temp_seam = os.path.join(root_dir, '.seam')

        #Generate directories
        os.makedirs(new_temp_seam, exist_ok = ok_exist_mode)
                    
        temp_metadict_root_directory = os.path.join(root_dir, "meta_dicts")
        os.makedirs(temp_metadict_root_directory, exist_ok = ok_exist_mode)
        
        temp_recipes_root_directory = os.path.join(root_dir, "Recipes")
        os.makedirs(temp_recipes_root_directory, exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Group Events"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Objects"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Processes"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Environments"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Filetypes"), exist_ok = ok_exist_mode)
        
        os.makedirs(os.path.join(temp_recipes_root_directory, "Perspectives"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Perspectives", "Samples"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Perspectives", "Projects"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_recipes_root_directory, "Perspectives", "Timelines"), exist_ok = ok_exist_mode)
        
        temp_typehash_root_directory = os.path.join(root_dir, "TypeHashes")
        os.makedirs(temp_typehash_root_directory, exist_ok = ok_exist_mode)

        temp_event_root_directory = os.path.join(root_dir, "Events")
        os.makedirs(temp_event_root_directory, exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_event_root_directory, "Proposed"), exist_ok = ok_exist_mode)
        os.makedirs(os.path.join(temp_event_root_directory, "History"), exist_ok = ok_exist_mode)

        temp_event_root_directory = os.path.join(root_dir, "Data")
        os.makedirs(temp_event_root_directory, exist_ok = ok_exist_mode)

        temp_template_root_directory = os.path.join(root_dir, "Templates")
        os.makedirs(temp_template_root_directory, exist_ok = ok_exist_mode)
        
        temp_log_root_directory = os.path.join(root_dir, "logs")
        os.makedirs(temp_log_root_directory, exist_ok = ok_exist_mode)

        #Create generic config file 
        config_dict = {
            'primary_root': new_temp_seam,
            'secondary_roots':[],
            'log_folder': temp_log_root_directory
            }
        
        config_filepath = os.path.join(root_dir, 'seam_config.json')
        
        with open(config_filepath, 'w', encoding='utf-8') as file:
            json.dump(config_dict, file, ensure_ascii=False, indent=4)