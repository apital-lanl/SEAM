# -*- coding: utf-8 -*-
"""
© 2025. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), 
which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security 
Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of 
Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf
a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, 
distribute copies to the public, perform publicly and display publicly, and to permit others to do so.

Author: Aaron Pital, Los Alamos National Lab
Created:  2025-09-25
Modified: 2025-09-25

Description: 80% vibe-coded GUI for running SEM stitching montage
"""
# SEAM modules
from SEAM.Core.MetaClass import Project
from SEAM.Analysis.ImageAnalysis import SEM, Keyence

# Python-native libraries
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random  # For demonstration purposes
from PIL import Image, ImageTk
Image.MAX_IMAGE_PIXELS = None   # disables warning on large file load
import traceback
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')  #Use backend to keep windows open
plt.ion()  # Turn on interactive mode


class SEMMontageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SEM Montage")
        self.root.geometry("1200x800")
        
        # Initialize variables for stitch options
        self.homography_algorithms = []
        self.alternate_save_location = ''
        self.dumb_stitch = True
          #"is there an image to display"; if not, show a random color block
        self.plotted_image = False
          #initialize 'display_image' to nothing
        self.display_image = None
        self.open_final_montage = tk.BooleanVar(value=False)
        self.save_final_annotated = tk.BooleanVar(value=False)
        self.open_final_annotated = tk.BooleanVar(value=False)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu
        self.create_menu()
        
        # Create PanedWindow to allow resizing
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Create left control panel and right canvas
        self.left_panel = ttk.Frame(self.paned_window)
        self.right_panel = ttk.Frame(self.paned_window)
        
        # Add panels to the paned window
        self.paned_window.add(self.left_panel, weight=1)
        self.paned_window.add(self.right_panel, weight=3)
        
        # Canvas for displaying images
        self.canvas = tk.Canvas(self.right_panel, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create alternate save location section at the top
        self.create_alternate_save_location_section()
        
        # Create stitch options section
        self.create_stitch_options_section()
        
        # Create control sections
        self.create_images_to_stitch_section()
        self.create_in_progress_section()
        self.create_completed_section()
        
        # Dictionary to store image collections
        self.image_collections = {}
        self.collection_stitch_type = {}
        
        # Track collection status
        self.collection_status = {}  # 'pending', 'in_progress', 'completed'
        
    def create_alternate_save_location_section(self):
        # Alternate save location section
        save_frame = ttk.Frame(self.left_panel)
        save_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(save_frame, text="Additional save location:").pack(anchor=tk.W)
        
        # Create a frame for the textbox and button
        input_frame = ttk.Frame(save_frame)
        input_frame.pack(fill=tk.X, expand=True)
        
        # Create the textbox
        self.save_location_var = tk.StringVar()
        self.save_location_entry = ttk.Entry(input_frame, textvariable=self.save_location_var)
        self.save_location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Bind click event to the textbox
        self.save_location_entry.bind("<Button-1>", self.select_save_location)
        
        # Add a browse button
        browse_btn = ttk.Button(input_frame, text="Browse", command=self.select_save_location)
        browse_btn.pack(side=tk.RIGHT)
    
    def select_save_location(self, event=None):
        """Open directory dialog to select alternate save location"""
        directory = filedialog.askdirectory(title="Select Alternate Save Location")
        if directory:
            self.alternate_save_location = directory
            self.save_location_var.set(directory)
    
    def create_stitch_options_section(self):
        # Stitch Options section
        self.options_frame = ttk.LabelFrame(self.left_panel, text="Stitch Options")
        self.options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create algorithm selection checkboxes
        self.sift_var = tk.BooleanVar()
        self.surf_var = tk.BooleanVar()
        self.akaze_var = tk.BooleanVar()
        self.orb_var = tk.BooleanVar()
        
        # Add checkboxes
        ttk.Checkbutton(self.options_frame, text="SIFT", variable=self.sift_var, 
                       command=self.update_algorithms).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(self.options_frame, text="SURF", variable=self.surf_var,
                       command=self.update_algorithms).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(self.options_frame, text="AKAZE", variable=self.akaze_var,
                       command=self.update_algorithms).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(self.options_frame, text="ORB", variable=self.orb_var,
                       command=self.update_algorithms).pack(anchor=tk.W, padx=5, pady=2)

        # Add option buttons
        ttk.Separator(self.options_frame, orient='horizontal').pack(fill='x', pady=4)

        ttk.Checkbutton(self.options_frame,
                        text="Open final montage",
                        variable=self.open_final_montage).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Checkbutton(self.options_frame,
                        text="Save annotated image",
                        variable=self.save_final_annotated).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Checkbutton(self.options_frame,
                        text="Open annotated image",
                        variable=self.open_final_annotated).pack(anchor=tk.W, padx=5, pady=2)
    
    def update_algorithms(self):
        """Update the homography algorithms list based on checkbox selection"""
        self.homography_algorithms = []
        
        if self.sift_var.get():
            self.homography_algorithms.append("SIFT")
        if self.surf_var.get():
            self.homography_algorithms.append("SURF")
        if self.akaze_var.get():
            self.homography_algorithms.append("AKAZE")
        if self.orb_var.get():
            self.homography_algorithms.append("ORB")
        
        # Update dumb_stitch based on algorithm selection
        self.dumb_stitch = len(self.homography_algorithms) == 0
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.menu_open)
        file_menu.add_command(label="Save", command=self.menu_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Properties menu
        properties_menu = tk.Menu(menubar, tearoff=0)
        properties_menu.add_command(label="Settings", command=self.menu_settings)
        menubar.add_cascade(label="Properties", menu=properties_menu)
        
        # Process Results menu
        process_menu = tk.Menu(menubar, tearoff=0)
        process_menu.add_command(label="Refine Montage", command=self.refine_montage)
        process_menu.add_command(label="Analyze Montage", command=self.analyze_montage)
        process_menu.add_command(label="Annotate Montage", command=self.annotate_montage)
        menubar.add_cascade(label="Process Results", menu=process_menu)
        
        self.root.config(menu=menubar)
    
    def create_images_to_stitch_section(self):
        # Images to Stitch section
        self.stitch_frame = ttk.LabelFrame(self.left_panel, text="Images to Stitch")
        self.stitch_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons frame
        btn_frame = ttk.Frame(self.stitch_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add buttons
        self.add_dir_btn = ttk.Button(btn_frame, text="Add by Directory", command=self.add_by_directory)
        self.add_dir_btn.pack(side=tk.LEFT, padx=5)
        
        self.add_files_btn = ttk.Button(btn_frame, text="Add by Files", command=self.add_by_files)
        self.add_files_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear Selected", command=self.clear_selected)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Listboxes frame
        list_frame = ttk.Frame(self.stitch_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Collections listbox with scrollbar
        collections_frame = ttk.Frame(list_frame)
        collections_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(collections_frame, text="Collections").pack(anchor=tk.W)
        
        self.collections_scrollbar = ttk.Scrollbar(collections_frame)
        self.collections_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.collections_listbox = tk.Listbox(collections_frame, 
                                              yscrollcommand=self.collections_scrollbar.set,
                                              selectmode=tk.EXTENDED,
                                              exportselection=False)
        self.collections_listbox.pack(fill=tk.BOTH, expand=True)
        self.collections_scrollbar.config(command=self.sync_scroll)
        
        # Size listbox with scrollbar
        size_frame = ttk.Frame(list_frame)
        size_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
        ttk.Label(size_frame, text="Number of Files").pack(anchor=tk.W)
        
        self.size_scrollbar = ttk.Scrollbar(size_frame)
        self.size_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.size_listbox = tk.Listbox(size_frame, 
                                       yscrollcommand=self.size_scrollbar.set,
                                       exportselection=False)
        self.size_listbox.pack(fill=tk.BOTH, expand=True)
        self.size_scrollbar.config(command=self.sync_scroll)
        
        # Run button
        self.run_btn = ttk.Button(self.stitch_frame, text="Run Selected", command=self.run_selected)
        self.run_btn.pack(fill=tk.X, padx=5, pady=5)
    
    def sync_scroll(self, *args):
        """Synchronize scrolling between Collections and Size listboxes"""
        self.collections_listbox.yview(*args)
        self.size_listbox.yview(*args)
    
    def create_in_progress_section(self):
        # In-progress section
        self.progress_frame = ttk.LabelFrame(self.left_panel, text="In-progress")
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Current task label
        self.task_label = ttk.Label(self.progress_frame, text="Current task: None")
        self.task_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
    
    def create_completed_section(self):
        # Completed section
        self.completed_frame = ttk.LabelFrame(self.left_panel, text="Completed")
        self.completed_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Completed listbox with scrollbar
        self.completed_scrollbar = ttk.Scrollbar(self.completed_frame)
        self.completed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.completed_listbox = tk.Listbox(self.completed_frame, yscrollcommand=self.completed_scrollbar.set)
        self.completed_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.completed_scrollbar.config(command=self.completed_listbox.yview)
    
    def add_by_directory(self):
        """Add images by selecting a directory"""
        directory = filedialog.askdirectory(title="Select Directory with Images")
        if not directory:
            return
            
        # Get all subdirectories as categories
        directories = {}
        
        # First check for images in the main directory
        main_dir_images = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and 
                          f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
        
        if main_dir_images:
            directories["Main Directory"] = main_dir_images
        
        # Then check subdirectories
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # Count image files in the subdirectory
                image_files = [os.path.join(item_path, f) for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)) and 
                              f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
                if image_files:
                    directories[item] = image_files
        
        if not directories:
            messagebox.showinfo("No Images", "No image files found in the selected directory or its subdirectories.")
            return
            
        # Add to collections dictionary
        for dir_key in list(directories.keys()):
            # Return a dict with categories split by filename parsing
            sub_category_dict = self.parse_filepaths_for_image_type(directories[dir_key])

            for cat_key in list(sub_category_dict.keys()):
                this_cat_dict = sub_category_dict[cat_key]
                collection_name = cat_key
                self.image_collections[collection_name] = this_cat_dict['filepaths']
                self.collection_stitch_type[collection_name] = this_cat_dict['stitch_type']
                self.collection_status[collection_name] = 'pending'
        
        # Update listboxes
        self.update_collections_listbox()
        
        # Select the newly added item
        last_index = self.collections_listbox.size() - 1
        self.collections_listbox.selection_set(last_index)
        self.collections_listbox.see(last_index)  # Ensure it's visible
    
    def add_by_files(self):
        """Add images by selecting individual files"""
        files = filedialog.askopenfilenames(title="Select Image Files", 
                                           filetypes=[("Image files", "*.png *.jpg *.jpeg *.tif *.tiff")])
        if not files:
            return
            
        # Group files by their parent directory
        directories = {}
        for file_path in files:
            parent_dir = os.path.basename(os.path.dirname(file_path))
            
            if parent_dir not in directories:
                directories[parent_dir] = []
            directories[parent_dir].append(file_path)
        
        # Add to collections dictionary
        for dir_key in list(directories.keys()):
            # Return a dict with categories split by filename parsing
            sub_category_dict = self.parse_filepaths_for_image_type(directories[dir_key])

            for cat_key in list(sub_category_dict.keys()):
                this_cat_dict = sub_category_dict[cat_key]
                collection_name = f"{cat_key}"
                self.image_collections[collection_name] = this_cat_dict['filepaths']
                self.collection_stitch_type[collection_name] = this_cat_dict['stitch_type']
                self.collection_status[collection_name] = 'pending'
        
        # Update listboxes
        self.update_collections_listbox()
        
        # Select the newly added item
        last_index = self.collections_listbox.size() - 1
        self.collections_listbox.selection_set(last_index)
        self.collections_listbox.see(last_index)  # Ensure it's visible

    def parse_filepaths_for_image_type(self, filepaths):
        """
        Specifically look for '_SE_' or '_BED-' flags from JEOL.
        TODO:
            - Add flags for other image stitching types
        """

        # Dict with each level 0 key as a common expression flagging a category of image
        flagged_type_names = {
            '_BED-':{
                'type_name': "JEOL,SEM,Backscatter",
                'short_type_name': "BD",
                'stitch_type': "JEOL,SEM"
                },
            '_SED':{
                'type_name': "JEOL,SEM,Secondary Electron",
                'short_type_name': "SE",
                'stitch_type': "JEOL,SEM"
                }
            }
        excluded_monikers = ["Mon"]

        # Initialize variables and clean input
        type_dict = {}

        if isinstance(filepaths, list):
            # Create list of regex names to check from keys of 'flagged_type_names'
            expressions = list(flagged_type_names.keys())

            # Parse each filename and check for category membership
            for filepath in filepaths:
                filename = os.path.basename(filepath)
                parent_directory = os.path.basename(os.path.dirname(filepath))

                for expression in expressions:
                    if expression in filename:
                        # Split the filename by the expression to unique front moniker
                        split_names = filename.split(expression)
                        # TODO: make use of the rest of the filename for better parsing
                        moniker = split_names[0]
                        display_name = f"[{parent_directory}]-[{expression}]-[{moniker}]"
                        
                        # Add to or update dict with filename and moniker
                        if display_name in type_dict:
                            type_dict[display_name]['filepaths'].append(filepath)
                        elif moniker not in excluded_monikers:
                            type_dict[display_name] = {
                                'filepaths': [filepath],
                                'moniker': moniker,
                                'type_name': flagged_type_names[expression]['type_name'],
                                'short_type_name': flagged_type_names[expression]['short_type_name'],
                                'stitch_type': flagged_type_names[expression]['stitch_type']
                            }
        
        return type_dict
             
    def update_collections_listbox(self):
        """Update the Collections and Size listboxes"""
        self.collections_listbox.delete(0, tk.END)
        self.size_listbox.delete(0, tk.END)
        
        for collection_name in self.image_collections:
            self.collections_listbox.insert(tk.END, collection_name)
            
            # Calculate total number of files in this collection
            total_files = len(self.image_collections[collection_name])
            self.size_listbox.insert(tk.END, str(total_files))
            
            # Apply styling based on status
            idx = self.collections_listbox.size() - 1
            status = self.collection_status.get(collection_name, 'pending')
            
            if status == 'in_progress':
                self.collections_listbox.itemconfig(idx, fg='yellow')  # Apply only color
                self.size_listbox.itemconfig(idx, fg='yellow')
            elif status == 'Completed':
                self.collections_listbox.itemconfig(idx, fg='gray')
                self.size_listbox.itemconfig(idx, fg='gray')
            elif status == 'StitchCompleted w/ DisplayError':
                self.collections_listbox.itemconfig(idx, fg='orange')
                self.size_listbox.itemconfig(idx, fg='orange')
            elif status == 'Failure':
                self.collections_listbox.itemconfig(idx, fg='red') 
                self.size_listbox.itemconfig(idx, fg='red')


    def clear_selected(self):
        """Clear selected items from the Collections listbox"""
        selected_indices = self.collections_listbox.curselection()
        if not selected_indices:
            return
            
        # Convert to list of collection names to delete
        to_delete = [self.collections_listbox.get(idx) for idx in selected_indices]
        
        # Delete from dictionary
        for collection_name in to_delete:
            if collection_name in self.image_collections:
                del self.image_collections[collection_name]
            if collection_name in self.collection_status:
                del self.collection_status[collection_name]
            if collection_name in self.collection_stitch_type:
                del self.collection_stitch_type[collection_name]
        
        # Update listboxes
        self.update_collections_listbox()
    
    def run_selected(self):
        """Process the selected collections"""
        selected_indices = self.collections_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Selection Required", "Please select collections to process.")
            return
            
        selected_collections = [self.collections_listbox.get(idx) for idx in selected_indices]
        
        # Process each selected collection
        for i, collection_name in enumerate(selected_collections):
            if collection_name in self.image_collections:
                # Update status to in_progress
                self.collection_status[collection_name] = 'in_progress'
                self.update_collections_listbox()
                
                self.task_label.config(text=f"Processing: {collection_name} ({i+1}/{len(selected_collections)})")
                self.root.update()
                
                # Process each category in the collection
                file_list = self.image_collections[collection_name]
                  #create a base savename
                basename_list = os.path.basename(file_list[0]).split('_')[0:-2]
                trial_types = []
                for part in basename_list:
                    if ('BED' in part) or ('SED' in part):
                        trial_types.append(part)
                dirname = os.path.dirname(os.path.dirname(file_list[0]))

                arg_dict = {
                    'guess_and_check': False, 
                    'show_guess_checking': False,
                    'show_matchpics': False,
                    'show_match_scatter': False,
                    'show_final_annotated': False,
                    'save_final_annotated': False,
                    'user_input': False,
                    'overright_GFA': True,
                    'algo': 'dumb',
                    'update_metadict': True,
                    'alternate_save_loaction': self.alternate_save_location,
                    'shift_dict': {},
                    'global_manual_shift': {
                        'manual_x_shift': 0,
                        'manual_y_shift': 0
                    },
                    'average_error_threshold': 50
                }
                #Flag for whether plot has been done already
                plotted_already = False
                #Flag for process dictionary (whether process finished or not)
                good_prcs_dict = False
                self.plotted_image = False

    
                try:
                    if self.dumb_stitch:
                        algorithm = 'dumb'
            
                        GFA = SEM.spatial_stitch(file_list, 
                                        guess_and_check=arg_dict['guess_and_check'],
                                        overright_GFA=arg_dict['overright_GFA'],
                                        update_metadict=arg_dict['update_metadict'],
                                        show_final_annotated=arg_dict['show_final_annotated'],
                                        save_final_annotated=arg_dict['save_final_annotated'],
                                        save_alternate_location=arg_dict['alternate_save_loaction'],
                                        shift_dict=arg_dict['shift_dict'],
                                        global_manual_shift=arg_dict['global_manual_shift'],
                                        )
            
                        interim_prcs_dict = {
                            'name': 'SEM stitch',
                            'status': 'completed',
                            'input_dict': arg_dict,
                            'files': file_list
                            }

                        good_prcs_dict = True

                        gfa_image = Image.fromarray(GFA)
                        gfa_image = gfa_image.convert("L")
                        self.plotted_image = True
                        self.display_image = gfa_image

                        savename = os.path.join(dirname, str(trial_types[0] + '_DumbStitch.png'))

                        if self.open_final_montage:
                            fig = plt.figure()
                            plt.imshow(GFA)
                            plt.title(f"GFA-{savename}")
                            fig.canvas.draw()
                            plt.pause(0.001)  # Small pause to allow the figure to be displayed
                        plotted_already = True
                    
                    else:
                        if len(self.homography_algorithms) > 0:
                            for algorithm in self.homography_algorithms:
                                arg_dict['algo'] = algorithm

                                #Reset flags for each iteration
                                plotted_already = False
                                good_prcs_dict = False
                    
                                GFA = SEM.homography_stitch(file_list, 
                                                guess_and_check=arg_dict['guess_and_check'],
                                                show_guess_checking=arg_dict['show_guess_checking'],
                                                show_matchpics=arg_dict['show_matchpics'],
                                                show_match_scatter=arg_dict['show_match_scatter'],
                                                show_final_annotated=arg_dict['show_final_annotated'],
                                                save_final_annotated=arg_dict['save_final_annotated'],
                                                user_input=arg_dict['user_input'],
                                                overright_GFA=arg_dict['overright_GFA'],
                                                algo=arg_dict['algo'],
                                                update_metadict=arg_dict['update_metadict'],
                                                save_alternate_location=arg_dict['alternate_save_loaction'],
                                                shift_dict=arg_dict['shift_dict'],
                                                global_manual_shift=arg_dict['global_manual_shift'],
                                                average_error_threshold=arg_dict['average_error_threshold'],
                                                )
                                
                                interim_prcs_dict = {
                                    'name': 'SEM stitch',
                                    'status': 'completed',
                                    'input_dict': arg_dict,
                                    'files': file_list
                                    }

                                good_prcs_dict = True
                                 
                                gfa_image = Image.fromarray(GFA)
                                gfa_image = gfa_image.convert("L")
                                self.plotted_image = True
                                self.display_image = gfa_image

                                savename = os.path.join(dirname, str(trial_types[0] + f'_{algorithm}.png'))
                                if self.open_final_montage:
                                    plt.imshow(GFA)
                                    plt.title(f"GFA-{savename}")
                                plotted_already = True
            
                        else:
                            algorithm = 'SIFT'
                            arg_dict['algo'] = algorithm
                
                            GFA = SEM.homography_stitch(file_list, 
                                            guess_and_check=arg_dict['guess_and_check'],
                                            show_guess_checking=arg_dict['show_guess_checking'],
                                            show_matchpics=arg_dict['show_matchpics'],
                                            show_match_scatter=arg_dict['show_match_scatter'],
                                            show_final_annotated=arg_dict['show_final_annotated'],
                                            save_final_annotated=arg_dict['save_final_annotated'],
                                            user_input=arg_dict['user_input'],
                                            overright_GFA=arg_dict['overright_GFA'],
                                            algo=arg_dict['algo'],
                                            update_metadict=arg_dict['update_metadict'],
                                            save_alternate_location=arg_dict['alternate_save_loaction'],
                                            shift_dict=arg_dict['shift_dict'],
                                            global_manual_shift=arg_dict['global_manual_shift'],
                                            average_error_threshold=arg_dict['average_error_threshold'],
                                            )
                
                            interim_prcs_dict = {
                                'name': 'SEM stitch',
                                'status': 'completed',
                                'input_dict': arg_dict,
                                'files': file_list
                                }

                            good_prcs_dict = True

                            self.plotted_image = True
                            gfa_image = Image.fromarray(GFA)
                            gfa_image = gfa_image.convert("L")
                            self.display_image = gfa_image
                        
                            savename = os.path.join(dirname, str(trial_types[0] + f'_{algorithm}.png'))
                            if self.open_final_montage:
                                plt.imshow(GFA)
                                plt.title(f"GFA-{savename}")
                            plotted_already = True

                except Exception as exc:
                    print(f"Failed on {algorithm} algorithm")
                    print(traceback.format_exc())
                    print()
                    
                    #If 'good_prcs_dict' hasn't flipped value (to True), no image was made
                    if not good_prcs_dict:
                        interim_prcs_dict = {
                            'name': 'SEM stitch',
                            'status': 'failed',
                            'error_trace': traceback.format_exc(),
                            'input_dict': arg_dict,
                            'files': file_list
                            }
                    #If the process went through 'good_prcs_dict', an image was saved 
                    else:
                        gfa_image = Image.fromarray(GFA)
                        gfa_image = gfa_image.convert("L")
                        self.plotted_image = True
                        self.display_image = gfa_image

                    print(f"Error on {algorithm} algorithm")
                    print()

                    #Dump the failure to an interim process file
                    savename = os.path.join(dirname, str(trial_types[0] + '-FailedGFA.png'))
                    if not plotted_already and self.open_final_montage:
                        plt.imshow(GFA)
                        plt.title(f"GFA-{savename}")
                        plt.savefig(savename)
                        plt.show()

                    Project.interim_process_dump(interim_prcs_dict)

                # Complete this collection
                self.progress_bar['value'] = 100
                self.root.update()
                
                # Update status to completed
                if good_prcs_dict and plotted_already:
                    self.collection_status[collection_name] = f'Completed'
                elif good_prcs_dict:
                    self.collection_status[collection_name] = f'StitchCompleted w/ DisplayError'
                else:
                    self.collection_status[collection_name] = f'Failure'
                self.update_collections_listbox()
                
                # Add completion summary to the Completed listbox
                summary = f"{collection_name}: {self.collection_status[collection_name]}"
                self.completed_listbox.insert(0, summary)
                
                # Display a final image (simulated)
                self.display_final_image(collection_name)
                
                # Reset progress bar
                self.root.after(1000)  # Show 100% for a moment
                self.progress_bar['value'] = 0
        
        # Reset task label
        self.task_label.config(text="Current task: None")
    
    
    def display_final_image(self, collection_name):
        """Display a final image in the canvas (simulated)"""
        # Clear canvas
        self.canvas.delete("all")
        
        # For demonstration, create a colored rectangle with text
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # If no image has been made yet, show a random color square
        if not self.plotted_image:

            # Random color for demonstration
            color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        
            self.canvas.create_rectangle(10, 10, width-10, height-10, fill=color)
            self.canvas.create_text(width/2, height/2, text=f"Montage for {collection_name}", 
                                   fill="white", font=("Arial", 24))
        elif type(self.display_image) != None:
            #populate canvas with plotted image
               # For very large images, use a more memory-efficient approach
            if width * height > 20000000:  # ~20 million pixels threshold
                # Use thumbnail instead of resize for better memory efficiency
                # Create a copy to avoid modifying the original
                img_copy = self.display_image.copy()
                img_copy.thumbnail((width, height), Image.LANCZOS)
                self.displayed_image = img_copy
            else:
                # For smaller images, use the normal resize method
                self.displayed_image = self.display_image.resize((width, height), Image.LANCZOS)
                
            # Create the PhotoImage
            self.photo = ImageTk.PhotoImage(self.displayed_image)
                
            # Update canvas
            self.canvas.delete("all")
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        else:
            # Random color for demonstration
            color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        
            self.canvas.create_rectangle(10, 10, width-10, height-10, fill=color)
            self.canvas.create_text(width/2, height/2, text=f"Montage for {collection_name}", 
                                   fill="white", font=("Arial", 24))

    
    # Menu callbacks
    def menu_open(self):
        messagebox.showinfo("Open", "Open functionality would go here")
    
    def menu_save(self):
        messagebox.showinfo("Save", "Save functionality would go here")
    
    def menu_settings(self):
        messagebox.showinfo("Settings", "Settings dialog would go here")
    
    def refine_montage(self):
        messagebox.showinfo("Refine Montage", "Refine montage functionality would go here")
    
    def analyze_montage(self):
        messagebox.showinfo("Analyze Montage", "Analyze montage functionality would go here")
    
    def annotate_montage(self):
        messagebox.showinfo("Annotate Montage", "Annotate montage functionality would go here")

if __name__ == "__main__":
    root = tk.Tk()
    app = SEMMontageApp(root)
    root.mainloop()