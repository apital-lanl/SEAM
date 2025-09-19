
#%%  SEM image stitching (2025-02-11)

 #SEAM modules
from MetaClass import SEAM
from ImageAnalysis import SEM, Keyence
 #Python-native labraries
from tkinter import Tk, filedialog
import traceback
import os
import matplotlib.pyplot as plt

global GFA

# dumb stitch- drop files by spatial location; not terrible, but off at edges
# 'False'- try and alighn images by homography; get image features and try to align them

dumb_stitch = True
other_save_location = r'F:\New SEM Montages'   # 'GUI' '' or filepath
if other_save_location == 'GUI':
    root = Tk()
    other_save_location = filedialog.askdirectory(title="Select an additional location to save stitch copies to.")
    root.destroy()
else:
    pass   #just pass 'other_save_location' 

######################################################################
##   SEM .tif image stitching      ###################################n
######################################################################

# # # Select the files to stitch
# # # NOTE: you'll need to click the console panel (prob bottom right of this window) to type Y/N

continue_check = True
filename_lists = []
f_list_idx = 0
while continue_check:
    
    # Get the names by user selection
    root = Tk()
    #root.withdraw()
    these_filenames = filedialog.askopenfilenames(title= 'Select images to stitch', filetypes = [("TIFs", '.tif')])
    root.destroy()
    
    # Sort to get images in left-to-right, top-to-bottom order by index (hopefully)
    filename_lists.append(SEM.sort_filenames(these_filenames))
    
    # Get and print representative filename to make it easeier to keep your place
    dirname = os.path.dirname(these_filenames[0])
    foldername = os.path.basename(dirname)
    example_filename = os.path.basename(these_filenames[0])
    print(f"{f_list_idx} \t {foldername}--{example_filename}")
    f_list_idx += 1
    
    # Ask if user want to add more
    user_report = input("Stitch another set of images (y/n or any key+ENTER to quit)").lower()
    if 'y' in user_report:
        continue_check = True
    else:
        continue_check = False
    

# Do the actual stitching and log results
for index, file_list in enumerate(filename_lists[0::]):
    print()
    print("###################################################################################################################")
    print()
    print("Working on: ")
    print(u'\t', "File ", index+1, ' of ', len(filename_lists))
    print(u'\t', os.path.dirname(file_list[0]))
    print()

    # alog options:    'ORB'   'SURF'   'SIFT'   'AKAZE'
    for algorithm in ['SIFT']:
        try:
            
            arg_dict = {
                'guess_and_check' : False, 
                'show_guess_checking' : False,
                'show_matchpics' : False,
                'show_match_scatter': False,
                'user_input' : False,
                'overright_GFA': True,
                'algo': algorithm,
                'update_metadict': True,
                'alternate_save_loaction': other_save_location,
                'shift_dict': {},
                'global_manual_shift': {
                    'manual_x_shift': 0,
                    'manual_y_shift': 0
                    },
                'average_error_threshold': 50
                }
            
            if dumb_stitch:
                SEM.spatial_stitch(file_list, 
                                guess_and_check = arg_dict['guess_and_check'],
                                overright_GFA = arg_dict['overright_GFA'],
                                update_metadict= arg_dict['update_metadict'],
                                save_alternate_location = arg_dict['alternate_save_loaction'],
                                shift_dict = arg_dict['shift_dict'],
                                global_manual_shift = arg_dict['global_manual_shift'],
                                  )
            else:
                SEM.homography_stitch(file_list, 
                                guess_and_check = arg_dict['guess_and_check'],
                                show_guess_checking = arg_dict['show_guess_checking'],
                                show_matchpics = arg_dict['show_matchpics'],
                                show_match_scatter = arg_dict['show_match_scatter'],
                                user_input = arg_dict['user_input'],
                                overright_GFA = arg_dict['overright_GFA'],
                                algo = arg_dict['algo'],
                                update_metadict= arg_dict['update_metadict'],
                                save_alternate_location = arg_dict['alternate_save_loaction'],
                                shift_dict = arg_dict['shift_dict'],
                                global_manual_shift = arg_dict['global_manual_shift'],
                                average_error_threshold = arg_dict['average_error_threshold'],
                                  )
            
            interim_prcs_dict = {
                'name': 'SEM stitch',
                'status': 'completed',
                'input_dict': arg_dict,
                'files':file_list
                }
            
            # SEAM.SEAM.interim_process_dump(interim_prcs_dict)
            
        except Exception as exc:
            print(f"Failed on {algorithm} algorithm")
            print(exc)
            print()
            
            interim_prcs_dict = {
                'name': 'SEM stitch',
                'status': 'failed',
                'error_trace': traceback.format_exc(),
                'input_dict': arg_dict,
                'files':file_list
                }

            # SEAM.SEAM.interim_process_dump(interim_prcs_dict)
            
            basename_list = os.path.basename(file_list[0]).split('_')[0:-2]
            trial_types = []
            for part in basename_list:
                if ('BED' in part) or ('SED' in part):
                    trial_types.append(part)
            dirname = os.path.dirname(os.path.dirname(file_list[0]))
            savename = os.path.join(dirname, str(trial_types[0] + '-FailedGFA.png'))
            
            plt.imshow(GFA)
            plt.title(f"Failed GFA- {basename}")
            plt.savefig(savename)
            plt.show()
            
            print(f"Failed on {algorithm} algorithm")
            print()
    
            
            
            

#%% Laser stitching

######################################################################
##   Laser .vk4 image stitching      #################################
######################################################################

 #SEAM modules
from SEAM import SEAM
from ImageAnalysis import Keyence
 #Python-native libraries
from tkinter import Tk, filedialog
import traceback
import os
import matplotlib.pyplot as plt

# prob bottom right of this window) to type Y/N

continue_check = True
filenames_list = []
while continue_check:
    # Get the names by user selection
    root = Tk()
    these_filenames = filedialog.askopenfilenames(title= 'Select images to stitch', filetypes = [("VK4-Keyence", '.vk4')])
    root.destroy()
    
    filenames_list.append(these_filenames)
    
    # Ask if user want to add more
    user_report = input("Stitch another set of images (y/n or any key+ENTER to quit)").lower()
    if 'y' in user_report:
        continue_check = True
    else:
        continue_check = False
        

# Do the actual stitching and log results
for idx, filenames in enumerate(filenames_list[1::]):
    print()
    print(f"Running {idx+1} of {len(filenames_list)}:")
    
    arg_dict = {
        'global_height_align' : False, 
        'tilt_constrain' : False,
        'report_height_stats' : False, 
        'optical_only' : False,
        'update_metadict': True
        }
    
    try:
        Keyence.vk4_stitch(filenames, 
                input_dict = arg_dict,
                update_metadict = True)
            
        interim_prcs_dict = {
            'name': 'VK4 Stitch',
            'status': 'completed',
            'input_dict': arg_dict,
            'files':filenames
            }
        
        SEAM.interim_process_dump(interim_prcs_dict)
    
    except Exception as exc:
        print(f"Failed on {idx+1} of {len(filenames_list)}")
        print()
        
        interim_prcs_dict = {
            'name': 'VK4 Stitch',
            'status': 'failed',
            'error_trace': traceback.format_exc(),
            'input_dict': arg_dict,
            'files':filenames
            }
        SEAM.interim_process_dump(interim_prcs_dict)
    
    
    
#%%