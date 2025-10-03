# -*- coding: utf-8 -*-
"""
Author:   Aaron Pital (Los Alamos National Lab)
Created:  2025-09-25
Modified: 2025-09-25

Description: 80% vibe-coded GUI for defect and blister annotation of images. 
    NOTE: Zooming in to large images places a large burden on memory and will be slow. 

"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
Image.MAX_IMAGE_PIXELS = None   # disables warning on large file load
import json
import os
import math

class ImageAnnotation:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.image = None
        self.displayed_image = None
        self.image_path = None
        self.canvas_image_id = None
        self.scale_factor = 1.0
        self.annotations = {}  # Dictionary to store annotations
        self.current_tool = None
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_shape = None
        self.current_color = "red"
        self.current_category = "unassigned"
        self.conversion_frame = None
        self.fiducial_count = 0
        self.fiducial_color = "yellow"
        self.fiducial_lines = []
        self.fiducial_lengths = []
        self.temp_points = []
        self.polygon_points = []
        self.pix_to_micron_conversion = 1   #Initialize to 1 arbitrarily 
        
        # Selection and modification variables
        self.selected_shape = None
        self.selected_shape_index = -1
        self.control_points = []
        self.dragging_point = None
        self.dragging_point_index = -1
          # Add a flag to track fiducial visibility
        self.fiducials_visible = True
          # Add this line to your existing __init__ method
        self.modification_mode = False
        
        # Create main layout
        self.create_menu()
        self.create_main_layout()
        
    
    def create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.load_image)
        file_menu.add_separator()
        file_menu.add_command(label="Save Annotations", command=self.save_annotations)
        file_menu.add_command(label="Load Annotations", command=self.load_annotations)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Metadata Menu
        metadata_menu = tk.Menu(self.menu_bar, tearoff=0)
        metadata_menu.add_command(label="View Metadata", command=self.view_metadata)
        metadata_menu.add_command(label="Edit Metadata", command=self.edit_metadata)
        self.menu_bar.add_cascade(label="Metadata", menu=metadata_menu)
        
        # Analysis Menu
        analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        analysis_menu.add_command(label="Annotation Summary", command=self.annotation_summary)
        self.menu_bar.add_cascade(label="Analysis", menu=analysis_menu)
        
        # Options Menu
        options_menu = tk.Menu(self.menu_bar, tearoff=0)
        options_menu.add_command(label="Preferences", command=self.show_preferences)
        self.menu_bar.add_cascade(label="Options", menu=options_menu)
        
        self.root.config(menu=self.menu_bar)
    
    
    def create_main_layout(self):
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas for the controls to make them scrollable
        self.controls_canvas = tk.Canvas(main_frame, width=300, bg="#f0f0f0")
        self.controls_canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        # Add a scrollbar to the controls canvas
        controls_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.controls_canvas.yview)
        controls_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Configure the canvas
        self.controls_canvas.configure(yscrollcommand=controls_scrollbar.set)
        self.controls_canvas.bind('<Configure>', lambda e: self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all")))
        
        # Create a frame inside the canvas for the controls
        self.controls_frame = tk.Frame(self.controls_canvas, bg="#f0f0f0", padx=10, pady=10)
        self.controls_canvas.create_window((0, 0), window=self.controls_frame, anchor=tk.NW, width=300)
        
        # Enable mousewheel scrolling
        self.controls_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.controls_canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.controls_canvas.bind_all("<Button-5>", self.on_mousewheel)
        
        # Canvas frame for image
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create image canvas scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create controls canvas
        self.canvas = tk.Canvas(canvas_frame, bg="gray", 
                               xscrollcommand=h_scrollbar.set, 
                               yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Bind events
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan_image)
        self.root.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.root.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.root.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_drawing)
        
        # Create controls
        self.create_image_controls()  # Add the image controls section first
        self.create_annotation_controls()
        self.create_fiducial_controls()
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    
    def create_annotation_controls(self):
        # Annotation frame
        annotation_frame = ttk.LabelFrame(self.controls_frame, text="Annotation")
        annotation_frame.pack(fill=tk.X, pady=10)
        
        # Selection and editing tools
        selection_frame = tk.Frame(annotation_frame)
        selection_frame.pack(fill=tk.X, pady=5)
        
        self.select_btn = ttk.Button(selection_frame, text="Select", command=lambda: self.set_tool("select"))
        self.select_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.modify_btn = ttk.Button(selection_frame, text="Modify", command=self.modify_selected)
        self.modify_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.clear_selected_btn = ttk.Button(selection_frame, text="Clear Selected", command=self.clear_selected)
        self.clear_selected_btn.grid(row=1, column=0, padx=5, pady=5)
        
        self.clear_all_btn = ttk.Button(selection_frame, text="Clear All", command=self.clear_all_annotations)
        self.clear_all_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Shape tools
        shapes_frame = tk.Frame(annotation_frame)
        shapes_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(shapes_frame, text="Shape:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.rectangle_btn = ttk.Button(shapes_frame, text="Rectangle", command=lambda: self.set_tool("rectangle"))
        self.rectangle_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.circle_btn = ttk.Button(shapes_frame, text="Circle", command=lambda: self.set_tool("circle"))
        self.circle_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.polygon_btn = ttk.Button(shapes_frame, text="Polygon", command=lambda: self.set_tool("polygon"))
        self.polygon_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Color selection
        color_frame = ttk.LabelFrame(annotation_frame, text="Color")
        color_frame.pack(fill=tk.X, pady=5)
        
        # Default color buttons
        white_btn = tk.Button(color_frame, bg="white", width=3, height=1, 
                             command=lambda: self.select_annotation("white", "unassigned"))
        white_btn.grid(row=0, column=0, padx=5, pady=5)
        
        gray_btn = tk.Button(color_frame, bg="gray", width=3, height=1, 
                            command=lambda: self.select_annotation("gray", "unassigned"))
        gray_btn.grid(row=0, column=1, padx=5, pady=5)
        
        defect_btn = tk.Button(color_frame, text="Defect", bg="yellow", width=5, height=1, 
                              command= lambda: self.select_annotation("yellow", "defect"))
        defect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        blister_btn = tk.Button(color_frame, text="Blister", bg="red", width=5, height=1, 
                           command= lambda: self.select_annotation("red", "blister"))
        blister_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Custom color button
        custom_color_btn = ttk.Button(color_frame, text="Point of Interest", 
                                     command=self.choose_custom_color)
        custom_color_btn.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Current color indicator
        self.color_indicator = tk.Canvas(color_frame, width=30, height=15, bg=self.current_color)
        self.color_indicator.grid(row=1, column=4, padx=5, pady=5)
        
    def select_annotation(self, color, category):
        self.set_category = category
        self.current_color = color
        
    
    def create_image_controls(self):
        # Image frame
        image_frame = ttk.LabelFrame(self.controls_frame, text="Image")
        image_frame.pack(fill=tk.X, pady=10)
        
        # Load image button
        load_image_btn = ttk.Button(image_frame, text="Load Image", command=self.load_image)
        load_image_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Zoom slider
        zoom_frame = tk.Frame(image_frame)
        zoom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT)
        self.zoom_var = tk.DoubleVar(value=1.0)
        self.zoom_slider = ttk.Scale(zoom_frame, from_=0.1, to=5.0, orient=tk.HORIZONTAL, 
                                    variable=self.zoom_var, command=self.on_zoom_slider_change)
        self.zoom_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.zoom_label = ttk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.RIGHT)
        
        # Filename section
        filename_frame = tk.Frame(image_frame)
        filename_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filename_frame, text="Filename:").pack(anchor=tk.W)
        self.filename_var = tk.StringVar(value="No image loaded")
        filename_entry = ttk.Entry(filename_frame, textvariable=self.filename_var, state="readonly")
        filename_entry.pack(fill=tk.X, pady=2)
        
        # Parent directory section
        parent_dir_frame = tk.Frame(image_frame)
        parent_dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(parent_dir_frame, text="Parent Directory:").pack(anchor=tk.W)
        self.parent_dir_var = tk.StringVar(value="")
        parent_dir_entry = ttk.Entry(parent_dir_frame, textvariable=self.parent_dir_var, state="readonly")
        parent_dir_entry.pack(fill=tk.X, pady=2)
        
        # Root directory section
        root_dir_frame = tk.Frame(image_frame)
        root_dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(root_dir_frame, text="Root Directory:").pack(anchor=tk.W)
        self.root_dir_var = tk.StringVar(value="")
        root_dir_entry = ttk.Entry(root_dir_frame, textvariable=self.root_dir_var, state="readonly")
        root_dir_entry.pack(fill=tk.X, pady=2)
    
    
    def on_zoom_slider_change(self, value):
        if not self.image:
            return
        
        # Update scale factor from slider
        self.scale_factor = float(value)
        
        # Update zoom label
        self.zoom_label.config(text=f"{int(self.scale_factor * 100)}%")
        
        # Update display
        self.display_image()
        
        
    def on_mousewheel(self, event):
        # Handle mousewheel scrolling for the controls panel
        if self.controls_canvas.winfo_containing(event.x_root, event.y_root) == self.controls_canvas:
            if event.num == 4 or event.delta > 0:  # Scroll up
                self.controls_canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:  # Scroll down
                self.controls_canvas.yview_scroll(1, "units")
        
    
    def create_fiducial_controls(self):
        # Fiducials frame
        self.fiducial_frame = ttk.LabelFrame(self.controls_frame, text="Fiducials")
        self.fiducial_frame.pack(fill=tk.X, pady=10)
        
        # Fiducial buttons
        draw_fiducial_btn = ttk.Button(self.fiducial_frame, text="Draw Length Fid.", 
                                      command=lambda: self.set_tool("fiducial"))
        draw_fiducial_btn.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        fiducial_color_btn = ttk.Button(self.fiducial_frame, text="Fiducial Color", 
                                       command=self.choose_fiducial_color)
        fiducial_color_btn.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Fiducial color indicator
        self.fiducial_color_indicator = tk.Canvas(self.fiducial_frame, width=30, height=15, bg=self.fiducial_color)
        self.fiducial_color_indicator.grid(row=0, column=2, padx=5, pady=5)
        
        # Clear and Hide buttons
        clear_fiducials_btn = ttk.Button(self.fiducial_frame, text="Clear Fiducials", 
                                        command=self.clear_fiducials)
        clear_fiducials_btn.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W+tk.E)
        
        self.hide_fiducials_btn = ttk.Button(self.fiducial_frame, text="Hide Fiducials", 
                                            command=self.toggle_fiducial_visibility)
        self.hide_fiducials_btn.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Container for fiducial measurements
        self.fiducial_container = tk.Frame(self.fiducial_frame)
        self.fiducial_container.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
    
    
    def toggle_fiducial_visibility(self):
        # Toggle the visibility state
        self.fiducials_visible = not self.fiducials_visible
        
        # Update the button text
        if self.fiducials_visible:
            self.hide_fiducials_btn.config(text="Hide Fiducials")
        else:
            self.hide_fiducials_btn.config(text="Show Fiducials")
        
        # Redraw the canvas to apply the change
        self.display_image()
    
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")])
        
        if file_path:
            try:
                self.image_path = file_path
                
                # Update status while loading
                self.status_bar.config(text=f"Loading image: {os.path.basename(file_path)}...")
                self.root.update()
                
                # Open the image
                self.image = Image.open(file_path)
                
                # Reset annotations dictionary
                self.annotations = {
                    "file_path": file_path,
                    "shapes": [],
                    "fiducials": []
                }
                
                # Calculate the minimum scale factor to fit the image in the canvas
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                # If canvas hasn't been drawn yet, use default values
                if canvas_width <= 1:
                    canvas_width = 800  # Default width
                if canvas_height <= 1:
                    canvas_height = 600  # Default height
                
                # Calculate scale factors to fit image in canvas
                width_scale = canvas_width / self.image.width
                height_scale = canvas_height / self.image.height
                
                # Use the smaller scale factor to ensure the entire image fits
                min_scale = min(width_scale, height_scale)
                
                # Set minimum zoom to fit the entire image
                min_zoom = min(min_scale, 0.1)  # Don't go below 0.1
                
                # Update zoom slider range
                self.zoom_slider.config(from_=min_zoom)
                
                # Set initial scale factor
                self.scale_factor = min_scale
                
                # For very large images, limit initial scale
                max_display_dimension = 2000  # Maximum initial dimension
                if self.image.width > max_display_dimension or self.image.height > max_display_dimension:
                    width_scale = max_display_dimension / self.image.width
                    height_scale = max_display_dimension / self.image.height
                    self.scale_factor = min(width_scale, height_scale)
                    
                    # Update status
                    self.status_bar.config(text=f"Large image detected. Initial scale set to {self.scale_factor:.2f}x")
                    self.root.update()
                
                # Update zoom slider and label
                self.zoom_var.set(self.scale_factor)
                self.zoom_label.config(text=f"{int(self.scale_factor * 100)}%")
                
                # Display the image
                self.display_image()
                
                # Update image information in the UI
                filename = os.path.basename(file_path)
                parent_dir = os.path.basename(os.path.dirname(file_path))
                root_dir = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
                
                self.filename_var.set(filename)
                self.parent_dir_var.set(parent_dir)
                self.root_dir_var.set(root_dir)
                
                # Update status
                self.status_bar.config(text=f"Loaded: {filename} ({self.image.width}x{self.image.height})")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")

    
    def display_image(self):
        if self.image:
            try:
                # Calculate new dimensions based on scale factor
                width = int(self.image.width * self.scale_factor)
                height = int(self.image.height * self.scale_factor)
                
                # Update status while processing
                self.status_bar.config(text=f"Resizing image to {width}x{height}...")
                self.root.update()
                
                # For very large images, use a more memory-efficient approach
                if width * height > 20000000:  # ~20 million pixels threshold
                    # Use thumbnail instead of resize for better memory efficiency
                    # Create a copy to avoid modifying the original
                    img_copy = self.image.copy()
                    img_copy.thumbnail((width, height), Image.LANCZOS)
                    self.displayed_image = img_copy
                else:
                    # For smaller images, use the normal resize method
                    self.displayed_image = self.image.resize((width, height), Image.LANCZOS)
                
                # Create the PhotoImage
                self.photo = ImageTk.PhotoImage(self.displayed_image)
                
                # Update canvas
                self.canvas.delete("all")
                self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
                self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
                
                # Redraw all annotations
                self.redraw_annotations()
                
                # Update status
                self.status_bar.config(text=f"Image displayed at {self.scale_factor:.2f}x zoom")
                
            except Exception as e:
                self.status_bar.config(text=f"Error displaying image: {str(e)}")
                print(f"Error displaying image: {str(e)}")
            
    
    def redraw_annotations(self):
        if not self.annotations or "shapes" not in self.annotations:
            return
            
        # Redraw shapes
        for shape in self.annotations["shapes"]:
            shape_type = shape["type"]
            coords = shape["coords"]
            color = shape["color"]
            
            # Scale coordinates
            scaled_coords = [c * self.scale_factor for c in coords]
            
            if shape_type == "rectangle":
                self.canvas.create_rectangle(scaled_coords, outline=color, width=2, tags="annotation")
            elif shape_type == "circle":
                self.canvas.create_oval(scaled_coords, outline=color, width=2, tags="annotation")
            elif shape_type == "polygon":
                self.canvas.create_polygon(scaled_coords, outline=color, fill="", width=2, tags="annotation")
        
        # Redraw fiducials only if they are visible
        if self.fiducials_visible:
            for fiducial in self.annotations.get("fiducials", []):
                coords = fiducial["coords"]
                color = fiducial["color"]
                length = fiducial["length"]
                
                # Scale coordinates
                scaled_coords = [c * self.scale_factor for c in coords]
                
                self.canvas.create_line(scaled_coords, fill=color, width=2, tags="fiducial")
                
                # Calculate midpoint for text
                mid_x = (scaled_coords[0] + scaled_coords[2]) / 2
                mid_y = (scaled_coords[1] + scaled_coords[3]) / 2
                
                # Display length
                self.canvas.create_text(mid_x, mid_y - 10, text=f"{length:.1f}px", 
                                       fill=color, tags="fiducial")
        
    def zoom(self, event):
        if not self.image:
            return
            
        # Get current position
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Store old scale factor
        old_scale = self.scale_factor
        
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:  # Zoom in
            self.scale_factor *= 1.1
        elif event.num == 5 or event.delta < 0:  # Zoom out
            self.scale_factor *= 0.9
        
        # Get minimum zoom level from slider configuration
        min_zoom = self.zoom_slider.cget("from")
        
        # Limit zoom level
        self.scale_factor = max(min_zoom, min(5.0, self.scale_factor))
        
        # For very large images, limit the maximum zoom to avoid memory issues
        max_pixels = 1000000000  # ~1 billion pixels
        if (self.image.width * self.scale_factor) * (self.image.height * self.scale_factor) > max_pixels:
            self.scale_factor = old_scale
            messagebox.showinfo("Zoom Limit", "Maximum zoom level reached for this image size.")
            return
        
        # Update zoom slider without triggering its callback
        self.zoom_var.set(self.scale_factor)
        self.zoom_label.config(text=f"{int(self.scale_factor * 100)}%")
        
        # Update display
        self.display_image()
        
        # Update status
        self.status_bar.config(text=f"Zoom: {self.scale_factor:.2f}x")
    
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
    
    def pan_image(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def set_tool(self, tool):
        # Exit modification mode when changing tools
        if tool != self.current_tool:
            self.modification_mode = False
            if tool != "select":
                self.clear_selection()
                
        self.current_tool = tool
        self.polygon_points = []  # Reset polygon points
        
        # Update status
        self.status_bar.config(text=f"Selected tool: {tool}")
    
    # def set_color(self, color):
    #     self.current_color = color
    #     self.color_indicator.config(bg=color)
        
    def set_category(self, category):
        '''
        Set the category applied to annotation.
        TODO: Add collective category reporting.
        Separate function to allow for complex category behaviour in the future.
        '''
        self.current_category = category
    
    def choose_custom_color(self):
        color = colorchooser.askcolor(initialcolor=self.current_color)
        if color[1]:
            self.current_color = color[1]
            self.color_indicator.config(bg=color[1])
        self.select_annotation(color[1], 'point_of_interest')
    
    def choose_fiducial_color(self):
        color = colorchooser.askcolor(initialcolor=self.fiducial_color)
        if color[1]:
            self.fiducial_color = color[1]
            self.fiducial_color_indicator.config(bg=color[1])
    
    def start_drawing(self, event):
        if not self.image or not self.current_tool:
            return
            
        # Get canvas coordinates
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        if self.current_tool == "polygon":
            # Add point to polygon
            self.polygon_points.append((self.start_x, self.start_y))
            
            # Draw point - use a unique tag for each point
            point_id = self.canvas.create_oval(
                self.start_x - 3, self.start_y - 3,
                self.start_x + 3, self.start_y + 3,
                fill=self.current_color, outline=self.current_color,
                tags=f"poly_point_{len(self.polygon_points)}")
            
            # If we have at least 2 points, draw line
            if len(self.polygon_points) > 1:
                prev_x, prev_y = self.polygon_points[-2]
                line_id = self.canvas.create_line(
                    prev_x, prev_y, self.start_x, self.start_y,
                    fill=self.current_color, width=2, 
                    tags=f"poly_line_{len(self.polygon_points)}")
            
            # Double click to finish polygon
            if len(self.polygon_points) > 2 and abs(self.polygon_points[0][0] - self.start_x) < 10 and abs(self.polygon_points[0][1] - self.start_y) < 10:
                self.end_polygon()
                return
                
        elif self.current_tool == "select":
            # Exit modification mode when selecting
            self.modification_mode = False
            
            # Check if we're clicking on a control point
            for point, index in self.control_points:
                point_coords = self.canvas.coords(point)
                if point_coords and len(point_coords) == 4:
                    x1, y1, x2, y2 = point_coords
                    if x1 <= self.start_x <= x2 and y1 <= self.start_y <= y2:
                        # We clicked on a control point, start dragging it
                        self.start_drag_control_point(event, index)
                        return
            
            # If we didn't click on a control point, try to select a shape
            self.clear_selection()
            self.try_select_shape_at_position(self.start_x, self.start_y)
        else:
            self.drawing = True
    
    def draw(self, event):
        if not self.image or not self.drawing:
            return
            
        # Get canvas coordinates
        curr_x = self.canvas.canvasx(event.x)
        curr_y = self.canvas.canvasy(event.y)
        
        # Delete previous temporary shape
        self.canvas.delete("temp")
        
        # Draw temporary shape
        if self.current_tool == "rectangle":
            self.current_shape = self.canvas.create_rectangle(
                self.start_x, self.start_y, curr_x, curr_y,
                outline=self.current_color, width=2, tags="temp")
        
        elif self.current_tool == "circle":
            self.current_shape = self.canvas.create_oval(
                self.start_x, self.start_y, curr_x, curr_y,
                outline=self.current_color, width=2, tags="temp")
        
        elif self.current_tool == "fiducial":
            self.current_shape = self.canvas.create_line(
                self.start_x, self.start_y, curr_x, curr_y,
                fill=self.fiducial_color, width=2, tags="temp")
            
            # Calculate length in raw image pixels
            dx = (curr_x / self.scale_factor) - (self.start_x / self.scale_factor)
            dy = (curr_y / self.scale_factor) - (self.start_y / self.scale_factor)
            length = math.sqrt(dx**2 + dy**2)
            
            # Show length in raw pixels
            self.canvas.create_text(
                (self.start_x + curr_x) / 2,
                (self.start_y + curr_y) / 2 - 10,
                text=f"{length:.1f}px",
                fill=self.fiducial_color,
                tags="temp")
    
    def end_drawing(self, event):
        if not self.image or not self.drawing and self.current_tool != "polygon":
            return
            
        # Get canvas coordinates
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # Convert to image coordinates (accounting for scale)
        start_x_img = self.start_x / self.scale_factor
        start_y_img = self.start_y / self.scale_factor
        end_x_img = end_x / self.scale_factor
        end_y_img = end_y / self.scale_factor
        
        # Save annotation based on tool type
        if self.current_tool == "rectangle":
            self.annotations["shapes"].append({
                "type": "rectangle",
                "coords": [start_x_img, start_y_img, end_x_img, end_y_img],
                "color": self.current_color,
                "category": self.current_category
            })
            
        elif self.current_tool == "circle":
            self.annotations["shapes"].append({
                "type": "circle",
                "coords": [start_x_img, start_y_img, end_x_img, end_y_img],
                "color": self.current_color,
                "category": self.current_category
            })
            
        elif self.current_tool == "fiducial":
            # Calculate length in raw image pixels
            dx = end_x_img - start_x_img
            dy = end_y_img - start_y_img
            length = math.sqrt(dx**2 + dy**2)
            
            # Add to annotations
            fiducial_id = len(self.annotations.get("fiducials", []))
            self.annotations.setdefault("fiducials", []).append({
                "id": fiducial_id,
                "coords": [start_x_img, start_y_img, end_x_img, end_y_img],
                "color": self.fiducial_color,
                "length": length
            })
            
            # Add to fiducial container
            self.add_fiducial_to_gui(fiducial_id, length)
        
        # Reset state
        self.drawing = False
        
        # Redraw annotations
        self.display_image()
    
    def end_polygon(self):
        if len(self.polygon_points) < 3:
            return
                
        # Convert to flat list and scale to image coordinates
        flat_points = []
        for x, y in self.polygon_points:
            flat_points.extend([x / self.scale_factor, y / self.scale_factor])
                
        # Save polygon annotation
        self.annotations["shapes"].append({
            "type": "polygon",
            "coords": flat_points,
            "color": self.current_color
        })
        
        # Clear temporary points
        self.canvas.delete("poly_point_*")
        self.canvas.delete("poly_line_*")
        self.polygon_points = []
        
        # Redraw annotations
        self.display_image()
        
    
    def select_shape_at_position(self, x, y):
        # Only clear selection if we're not in modification mode
        if not self.modification_mode:
            self.clear_selection()
        
        # Try to select a shape
        self.try_select_shape_at_position(x, y)
    
    def try_select_shape_at_position(self, x, y):
        # Convert to image coordinates
        img_x = x / self.scale_factor
        img_y = y / self.scale_factor
        
        # Check each shape
        for i, shape in enumerate(self.annotations.get("shapes", [])):
            shape_type = shape["type"]
            coords = shape["coords"]
            
            if shape_type == "rectangle":
                x1, y1, x2, y2 = coords
                # Make sure x1,y1 is top-left and x2,y2 is bottom-right
                if x1 > x2: x1, x2 = x2, x1
                if y1 > y2: y1, y2 = y2, y1
                
                if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                    self.selected_shape_index = i
                    self.selected_shape = shape
                    self.highlight_selected_shape()
                    return True
                    
            elif shape_type == "circle":
                x1, y1, x2, y2 = coords
                # Calculate center and radius
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                radius_x = abs(x2 - x1) / 2
                radius_y = abs(y2 - y1) / 2
                
                # Check if point is inside ellipse
                if ((img_x - center_x) / radius_x) ** 2 + ((img_y - center_y) / radius_y) ** 2 <= 1:
                    self.selected_shape_index = i
                    self.selected_shape = shape
                    self.highlight_selected_shape()
                    return True
                    
            elif shape_type == "polygon":
                # Check if point is inside polygon
                points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
                if self.point_in_polygon(img_x, img_y, points):
                    self.selected_shape_index = i
                    self.selected_shape = shape
                    self.highlight_selected_shape()
                    return True
        
        return False
    
    def point_in_polygon(self, x, y, polygon):
        # Ray casting algorithm to determine if point is in polygon
        inside = False
        j = len(polygon) - 1
        
        for i in range(len(polygon)):
            if ((polygon[i][1] > y) != (polygon[j][1] > y)) and \
               (x < (polygon[j][0] - polygon[i][0]) * (y - polygon[i][1]) / 
                (polygon[j][1] - polygon[i][1]) + polygon[i][0]):
                inside = not inside
            j = i
            
        return inside
    
    def highlight_selected_shape(self):
        if not self.selected_shape:
            return
            
        shape_type = self.selected_shape["type"]
        coords = self.selected_shape["coords"]
        color = self.selected_shape["color"]
        
        # Scale coordinates
        scaled_coords = [c * self.scale_factor for c in coords]
        
        if shape_type == "rectangle":
            self.canvas.create_rectangle(scaled_coords, outline="blue", width=4, dash=(5,5), tags="selection")
        elif shape_type == "circle":
            self.canvas.create_oval(scaled_coords, outline="blue", width=4, dash=(5,5), tags="selection")
        elif shape_type == "polygon":
            self.canvas.create_polygon(scaled_coords, outline="blue", fill="", width=4, dash=(5,5), tags="selection")
    
    def clear_selection(self):
        # Exit modification mode
        self.modification_mode = False
        self.modify_btn.config(text="Modify")
        
        # Clear selection visuals
        self.canvas.delete("selection")
        self.canvas.delete("control_point")
        self.selected_shape = None
        self.selected_shape_index = -1
        self.control_points = []
    
    def modify_selected(self):
        if not self.selected_shape:
            messagebox.showinfo("Info", "No shape selected. Please select a shape first.")
            return
            
        # Clear any existing control points
        self.canvas.delete("control_point")
        self.control_points = []
        
        shape_type = self.selected_shape["type"]
        coords = self.selected_shape["coords"]
        
        if shape_type == "rectangle" or shape_type == "circle":
            # Create control points at corners
            x1, y1, x2, y2 = coords
            
            # Scale coordinates
            x1 *= self.scale_factor
            y1 *= self.scale_factor
            x2 *= self.scale_factor
            y2 *= self.scale_factor
            
            # Create control points
            self.create_control_point(x1, y1, 0)
            self.create_control_point(x2, y1, 1)
            self.create_control_point(x2, y2, 2)
            self.create_control_point(x1, y2, 3)
            
        elif shape_type == "polygon":
            # Create control points at each vertex
            for i in range(0, len(coords), 2):
                x = coords[i] * self.scale_factor
                y = coords[i+1] * self.scale_factor
                self.create_control_point(x, y, i//2)
    
    def create_control_point(self, x, y, index):
        point = self.canvas.create_rectangle(
            x - 5, y - 5, x + 5, y + 5,
            fill="blue", outline="white", tags=f"control_point control_point_{index}")
        
        self.control_points.append((point, index))
        
        # Bind events to control point
        self.canvas.tag_bind(point, "<ButtonPress-1>", lambda e, idx=index: self.start_drag_control_point(e, idx))
        self.canvas.tag_bind(point, "<B1-Motion>", self.drag_control_point)
        self.canvas.tag_bind(point, "<ButtonRelease-1>", self.end_drag_control_point)
    
    def start_drag_control_point(self, event, index):
        self.dragging_point = True
        self.dragging_point_index = index
    
    def drag_control_point(self, event):
        if not self.dragging_point:
            return
            
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Update control point position
        for point, index in self.control_points:
            if index == self.dragging_point_index:
                self.canvas.coords(point, x - 5, y - 5, x + 5, y + 5)
                break
    
    def end_drag_control_point(self, event):
        if not self.dragging_point:
            return
            
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        img_x = x / self.scale_factor
        img_y = y / self.scale_factor
        
        # Update shape coordinates
        shape_type = self.selected_shape["type"]
        coords = self.selected_shape["coords"]
        
        if shape_type == "rectangle" or shape_type == "circle":
            if self.dragging_point_index == 0:  # Top-left
                coords[0] = img_x
                coords[1] = img_y
            elif self.dragging_point_index == 1:  # Top-right
                coords[2] = img_x
                coords[1] = img_y
            elif self.dragging_point_index == 2:  # Bottom-right
                coords[2] = img_x
                coords[3] = img_y
            elif self.dragging_point_index == 3:  # Bottom-left
                coords[0] = img_x
                coords[3] = img_y
        
        elif shape_type == "polygon":
            # Update polygon vertex
            coords[self.dragging_point_index * 2] = img_x
            coords[self.dragging_point_index * 2 + 1] = img_y
        
        # Update annotation
        self.annotations["shapes"][self.selected_shape_index] = self.selected_shape
        
        # Reset dragging state
        self.dragging_point = False
        self.dragging_point_index = -1
        
        # Redraw everything
        self.display_image()
        self.highlight_selected_shape()
        self.modify_selected()  # Recreate control points
    
    def clear_selected(self):
        if self.selected_shape_index >= 0:
            # Remove from annotations
            self.annotations["shapes"].pop(self.selected_shape_index)
            
            # Clear selection
            self.clear_selection()
            
            # Redraw
            self.display_image()
    
    def clear_all_annotations(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all annotations?"):
            # Clear annotations
            if "shapes" in self.annotations:
                self.annotations["shapes"] = []
            
            # Clear selection
            self.clear_selection()
            
            # Redraw
            self.display_image()
        
    
    def add_fiducial_to_gui(self, fiducial_id, length):
        # Create a new row for this fiducial
        row_frame = tk.Frame(self.fiducial_container)
        row_frame.pack(fill=tk.X, pady=2)
        
        # Add label
        label = ttk.Label(row_frame, text=f"Fiducial {fiducial_id}: {length:.2f} px")
        label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Add length display
        length_var = tk.StringVar(value=f"{length:.2f} px")
        length_label = ttk.Label(row_frame, textvariable=length_var)
        length_label.grid(row=0, column=1, padx=5)
        
        # Add fiducial length input
        ttk.Label(row_frame, text="Fiducial Length:").grid(row=0, column=2, padx=5)
        length_entry = ttk.Entry(row_frame, width=10)
        length_entry.grid(row=0, column=3, padx=5)
        
        # Bind the entry to recalculate conversion when value changes
        length_entry.bind("<Return>", lambda e, fid=fiducial_id, px=length: self.update_fiducial_length(e, fid, px))
        length_entry.bind("<FocusOut>", lambda e, fid=fiducial_id, px=length: self.update_fiducial_length(e, fid, px))
        
        # Store the entry widget and variables in the fiducial data
        if "fiducials" in self.annotations and len(self.annotations["fiducials"]) > fiducial_id:
            self.annotations["fiducials"][fiducial_id]["entry_widget"] = length_entry
            self.annotations["fiducials"][fiducial_id]["length_var"] = length_var
        
    
    def update_fiducial_length(self, event, fiducial_id, pixel_length):
        """Update the fiducial length and recalculate the conversion factor"""
        entry_widget = event.widget
        try:
            # Get the entered value
            entered_length = float(entry_widget.get())
            
            # Store the real-world length in the fiducial data
            if "fiducials" in self.annotations and len(self.annotations["fiducials"]) > fiducial_id:
                self.annotations["fiducials"][fiducial_id]["real_length"] = entered_length
                
                # Calculate conversion for this fiducial (microns per pixel)
                conversion = entered_length / pixel_length
                self.annotations["fiducials"][fiducial_id]["conversion"] = conversion
                
                # Recalculate the average conversion factor
                self.recalculate_conversion_factor()
                
                # Update the status bar
                self.status_bar.config(text=f"Conversion factor updated: {self.pix_to_micron_conversion:.6f} microns/pixel")
        except ValueError:
            # Invalid input
            messagebox.showerror("Error", "Please enter a valid number for the fiducial length.")
            
    
    def recalculate_conversion_factor(self):
        """Recalculate the average conversion factor from all fiducials with real-world lengths"""
        conversion_factors = []
        
        for fiducial in self.annotations.get("fiducials", []):
            if "real_length" in fiducial and "length" in fiducial:
                conversion = fiducial["real_length"] / fiducial["length"]
                conversion_factors.append(conversion)
        
        if conversion_factors:
            # Calculate average conversion factor
            self.pix_to_micron_conversion = sum(conversion_factors) / len(conversion_factors)
            
            # Create or update the conversion factor display
            if not hasattr(self, 'conversion_frame'):
                self.conversion_frame = tk.Frame(self.fiducial_frame)
                self.conversion_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
                
                ttk.Label(self.conversion_frame, text="Conversion Factor:").grid(row=0, column=0, padx=5, sticky=tk.W)
                self.conversion_label = ttk.Label(self.conversion_frame, text=f"{self.pix_to_micron_conversion:.6f} microns/pixel")
                self.conversion_label.grid(row=0, column=1, padx=5, sticky=tk.W)
            else:
                # Update the existing label
                self.conversion_label.config(text=f"{self.pix_to_micron_conversion:.6f} microns/pixel")
    
    
    def clear_fiducials(self):
        # Clear fiducials from annotations
        if "fiducials" in self.annotations:
            self.annotations["fiducials"] = []
        
        # Clear fiducials from GUI
        for widget in self.fiducial_container.winfo_children():
            widget.destroy()
        
        # Redraw
        self.display_image()
    
    def save_annotations(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "No image loaded.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=os.path.splitext(os.path.basename(self.image_path))[0] + "_annotations.json"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.annotations, f, indent=2)
                self.status_bar.config(text=f"Annotations saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save annotations: {e}")
    
    def load_annotations(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.annotations = json.load(f)
                
                # Load the associated image if not already loaded
                if "file_path" in self.annotations and self.annotations["file_path"] != self.image_path:
                    if os.path.exists(self.annotations["file_path"]):
                        self.image_path = self.annotations["file_path"]
                        self.image = Image.open(self.image_path)
                        self.displayed_image = self.image.copy()
                        self.display_image()
                    else:
                        messagebox.showwarning("Warning", "Original image not found. Annotations loaded but image path is invalid.")
                
                # Redraw annotations
                self.display_image()
                
                # Rebuild fiducial GUI
                for widget in self.fiducial_container.winfo_children():
                    widget.destroy()
                    
                for fiducial in self.annotations.get("fiducials", []):
                    self.add_fiducial_to_gui(fiducial["id"], fiducial["length"])
                
                self.status_bar.config(text=f"Annotations loaded from {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load annotations: {e}")
    
    def view_metadata(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "No image loaded.")
            return
            
        metadata = {}
        try:
            img = Image.open(self.image_path)
            metadata["Format"] = img.format
            metadata["Size"] = f"{img.width} x {img.height}"
            metadata["Mode"] = img.mode
            
            # Try to get EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                if exif:
                    for tag, value in exif.items():
                        if tag in Image.TAGS:
                            metadata[Image.TAGS[tag]] = value
        except Exception as e:
            messagebox.showerror("Error", f"Could not read metadata: {e}")
            return
            
        # Display metadata
        metadata_window = tk.Toplevel(self.root)
        metadata_window.title("Image Metadata")
        metadata_window.geometry("400x300")
        
        # Create a text widget to display metadata
        text = tk.Text(metadata_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insert metadata
        for key, value in metadata.items():
            text.insert(tk.END, f"{key}: {value}\n")
        
        text.config(state=tk.DISABLED)
    
    def edit_metadata(self):
        messagebox.showinfo("Info", "Metadata editing functionality not implemented yet.")
    
    def annotation_summary(self):
        messagebox.showinfo("Info", "Analysis functionality not implemented yet.")
    
    def show_preferences(self):
        messagebox.showinfo("Info", "Preferences functionality not implemented yet.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotation(root)
    root.mainloop()
