# -*- coding: utf-8 -*-
"""
Author:   Aaron Pital (Los Alamos National Lab)
Created:  2025-09-25
Modified: 2025-09-25

Description: 80% vibe-coded GUI for running SEM stitching montage
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random  # For demonstration purposes
from PIL import Image, ImageTk

class SEMMontageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SEM Montage")
        self.root.geometry("1200x800")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu
        self.create_menu()
        
        # Create left control panel and right canvas
        self.left_panel = ttk.Frame(self.main_frame, width=400)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for displaying images
        self.canvas = tk.Canvas(self.right_panel, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create control sections
        self.create_images_to_stitch_section()
        self.create_in_progress_section()
        self.create_completed_section()
        
        # Dictionary to store image collections
        self.image_collections = {}
        
        # Track collection status
        self.collection_status = {}  # 'pending', 'in_progress', 'completed'
        
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
        
        ttk.Label(size_frame, text="Size").pack(anchor=tk.W)
        
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
        categories = {}
        
        # First check for images in the main directory
        main_dir_images = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and 
                          f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
        
        if main_dir_images:
            categories["Main Directory"] = main_dir_images
        
        # Then check subdirectories
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # Count image files in the subdirectory
                image_files = [f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)) and 
                              f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
                if image_files:
                    categories[item] = image_files
        
        if not categories:
            messagebox.showinfo("No Images", "No image files found in the selected directory or its subdirectories.")
            return
            
        # Add to collections dictionary
        collection_name = os.path.basename(directory)
        self.image_collections[collection_name] = categories
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
        categories = {}
        for file_path in files:
            parent_dir = os.path.basename(os.path.dirname(file_path))
            file_name = os.path.basename(file_path)
            
            if parent_dir not in categories:
                categories[parent_dir] = []
            categories[parent_dir].append(file_name)
        
        # Add to collections dictionary
        collection_name = f"Files Selection ({len(files)} files)"
        self.image_collections[collection_name] = categories
        self.collection_status[collection_name] = 'pending'
        
        # Update listboxes
        self.update_collections_listbox()
        
        # Select the newly added item
        last_index = self.collections_listbox.size() - 1
        self.collections_listbox.selection_set(last_index)
        self.collections_listbox.see(last_index)  # Ensure it's visible
    
    def update_collections_listbox(self):
        """Update the Collections and Size listboxes"""
        self.collections_listbox.delete(0, tk.END)
        self.size_listbox.delete(0, tk.END)
        
        for collection_name in self.image_collections:
            self.collections_listbox.insert(tk.END, collection_name)
            
            # Calculate total number of files in this collection
            total_files = sum(len(files) for files in self.image_collections[collection_name].values())
            self.size_listbox.insert(tk.END, str(total_files))
            
            # Apply styling based on status
            idx = self.collections_listbox.size() - 1
            status = self.collection_status.get(collection_name, 'pending')
            
            if status == 'in_progress':
                self.collections_listbox.itemconfig(idx, fg='red')  # Apply only color
                self.size_listbox.itemconfig(idx, fg='red')
            elif status == 'completed':
                self.collections_listbox.itemconfig(idx, fg='gray')  # Apply only color
                self.size_listbox.itemconfig(idx, fg='gray')
    
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
                categories = self.image_collections[collection_name]
                total_steps = len(categories)
                
                for step, (category, files) in enumerate(categories.items()):
                    # Update progress
                    progress = (step / total_steps) * 100
                    self.progress_bar['value'] = progress
                    self.task_label.config(text=f"Processing: {collection_name} - {category}")
                    self.root.update()
                    
                    # Simulate processing time
                    self.root.after(500)  # 500ms delay to simulate processing
                
                # Complete this collection
                self.progress_bar['value'] = 100
                self.root.update()
                
                # Update status to completed
                self.collection_status[collection_name] = 'completed'
                self.update_collections_listbox()
                
                # Add completion summary to the Completed listbox
                summary = f"Completed: {collection_name} - {len(categories)} categories, {sum(len(files) for files in categories.values())} files"
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
