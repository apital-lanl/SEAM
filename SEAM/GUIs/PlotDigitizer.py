import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import random
import os
import cv2
from PIL import Image, ImageTk, ImageEnhance
import json
import uuid
from scipy.interpolate import interp1d

class Figure_Digitizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Figure Digitizer")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.image_path = None
        self.original_image = None
        self.displayed_image = None
        self.axes = {}  # Dictionary to store axes information
        self.extracted_data = {}  # Dictionary to store extracted data
        self.current_dataset = None
        self.current_axes = None
        self.magnification = 5
        self.min_magnification = 5  # Will be updated when image is loaded
        self.max_magnification = 5  # Will be updated when image is loaded
        self.crosshair_color = "red"
        self.extraction_mode = None  # 'add', 'adjust', 'delete'
        self.current_algorithm = "Averaging Window"
        self.delta_x = 10
        self.delta_y = 10
        self.brush_width = 5
        self.foreground_color = "#000000"  # Black
        self.background_color = "#FFFFFF"  # White
        self.current_color = self.foreground_color
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create and configure the three panels
        self.create_panels()
        
        # Populate left panel
        self.populate_left_panel()
        
        # Create middle panel content
        self.create_middle_panel_content()
        
        # Initialize right panel with default context (Image Settings)
        self.show_image_settings_context()
        
        # Bind events
        self.bind_events()
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load plot", command=self.load_image)
        file_menu.add_command(label="Save plot", command=self.save_image)
        file_menu.add_command(label="Load from PDF", command=self.load_from_pdf)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Project menu
        project_menu = tk.Menu(menubar, tearoff=0)
        project_menu.add_command(label="Save project", command=self.save_project)
        project_menu.add_command(label="Load project", command=self.load_project)
        project_menu.add_command(label="Link project", command=self.link_project)
        menubar.add_cascade(label="Project", menu=project_menu)
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        data_menu.add_command(label="Save Data as single CSV", command=self.save_data_single_csv)
        data_menu.add_command(label="Save Data as individual CSV", command=self.save_data_individual_csv)
        menubar.add_cascade(label="Data", menu=data_menu)
        
        self.root.config(menu=menubar)
    
    def create_panels(self):
        # Create left panel (scrollable)
        self.left_frame = ttk.Frame(self.main_frame, width=300)
        self.left_canvas = tk.Canvas(self.left_frame)
        self.left_scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.left_canvas.yview)
        self.left_scrollable_frame = ttk.Frame(self.left_canvas)
        
        self.left_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        )
        
        self.left_canvas.create_window((0, 0), window=self.left_scrollable_frame, anchor="nw")
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_canvas.pack(side="left", fill="both", expand=True)
        self.left_scrollbar.pack(side="right", fill="y")
        
        # Create middle panel (scrollable)
        self.middle_frame = ttk.Frame(self.main_frame)
        self.middle_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Create right panel (scrollable)
        self.right_frame = ttk.Frame(self.main_frame, width=300)
        self.right_canvas = tk.Canvas(self.right_frame)
        self.right_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.right_canvas.yview)
        self.right_scrollable_frame = ttk.Frame(self.right_canvas)
        
        self.right_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
        )
        
        self.right_canvas.create_window((0, 0), window=self.right_scrollable_frame, anchor="nw")
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.right_canvas.pack(side="left", fill="both", expand=True)
        self.right_scrollbar.pack(side="right", fill="y")
        
        # Configure the grid weights
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_columnconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
    
    def populate_left_panel(self):
        # Import Plot Section
        import_frame = ttk.LabelFrame(self.left_scrollable_frame, text="Import Plot")
        import_frame.pack(fill="x", padx=5, pady=5, expand=True)
        
        ttk.Button(import_frame, text="Load image", command=self.load_image).pack(fill="x", padx=5, pady=2)
        ttk.Button(import_frame, text="Edit image", command=lambda: self.show_image_settings_context()).pack(fill="x", padx=5, pady=2)
        
        self.filename_var = tk.StringVar()
        self.filename_var.set("No file loaded")
        ttk.Label(import_frame, textvariable=self.filename_var, wraplength=280).pack(fill="x", padx=5, pady=2)
        
        # Define Plot Details Section
        plot_details_frame = ttk.LabelFrame(self.left_scrollable_frame, text="Define Plot Details")
        plot_details_frame.pack(fill="x", padx=5, pady=5, expand=True)
        
        # Plot type subsection
        plot_type_frame = ttk.Frame(plot_details_frame)
        plot_type_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(plot_type_frame, text="Plot type:").pack(side="left", padx=5)
        self.plot_type_var = tk.StringVar()
        plot_type_combo = ttk.Combobox(plot_type_frame, textvariable=self.plot_type_var)
        plot_type_combo['values'] = ('XY Plot', 'Ternary Diagram', 'Image', 'Bar Chart', 'Polar Plot')
        plot_type_combo.current(0)
        plot_type_combo.pack(side="left", padx=5, fill="x", expand=True)
        plot_type_combo.bind("<<ComboboxSelected>>", self.on_plot_type_change)
        
        # View Settings subsection
        view_settings_frame = ttk.LabelFrame(plot_details_frame, text="View Settings")
        view_settings_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(view_settings_frame, text="Crosshair color", command=self.change_crosshair_color).pack(fill="x", padx=5, pady=2)
        
        # Magnifier slider
        magnifier_frame = ttk.Frame(view_settings_frame)
        magnifier_frame.pack(fill="x", padx=5, pady=2)
        
        self.magnifier_label_var = tk.StringVar(value="Magnifier: 10 x 10 pixels")
        ttk.Label(magnifier_frame, textvariable=self.magnifier_label_var).pack(side="top", anchor="w")
        
        self.magnifier_var = tk.DoubleVar(value=5)
        self.magnifier_slider = ttk.Scale(magnifier_frame, from_=5, to=5, orient="horizontal", 
                                          variable=self.magnifier_var, command=self.update_magnification)
        self.magnifier_slider.pack(fill="x", padx=5, pady=2)
        
        # Axes subsection
        axes_frame = ttk.LabelFrame(plot_details_frame, text="Axes")
        axes_frame.pack(fill="x", padx=5, pady=2)
        
        self.axes_listbox = tk.Listbox(axes_frame, height=5, exportselection=0)
        self.axes_listbox.pack(fill="x", padx=5, pady=2)
        self.axes_listbox.bind('<<ListboxSelect>>', self.on_axes_select)
        
        axes_buttons_frame = ttk.Frame(axes_frame)
        axes_buttons_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(axes_buttons_frame, text="Add Axes", command=self.add_axes).pack(side="left", padx=2)
        ttk.Button(axes_buttons_frame, text="Change Axes", command=self.change_axes).pack(side="left", padx=2)
        ttk.Button(axes_buttons_frame, text="Clear Axes", command=self.clear_axes).pack(side="left", padx=2)
        ttk.Button(axes_buttons_frame, text="Clear All", command=self.clear_all_axes).pack(side="left", padx=2)
        
        # Extracted Data subsection
        extracted_data_frame = ttk.LabelFrame(plot_details_frame, text="Extracted Data")
        extracted_data_frame.pack(fill="x", padx=5, pady=2)
        
        self.data_listbox = tk.Listbox(extracted_data_frame, height=5, selectmode=tk.MULTIPLE, exportselection=0)
        self.data_listbox.pack(fill="x", padx=5, pady=2)
        self.data_listbox.bind('<<ListboxSelect>>', self.on_data_select)
        
        data_buttons_frame = ttk.Frame(extracted_data_frame)
        data_buttons_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(data_buttons_frame, text="Display Data", command=self.display_data).pack(side="left", padx=2)
        ttk.Button(data_buttons_frame, text="Save Data", command=self.save_data).pack(side="left", padx=2)
        ttk.Button(data_buttons_frame, text="Show Data Overlayed", command=self.show_data_overlayed).pack(side="left", padx=2)
        
        # Measurements Section
        measurements_frame = ttk.LabelFrame(self.left_scrollable_frame, text="Measurements")
        measurements_frame.pack(fill="x", padx=5, pady=5, expand=True)
        
        ttk.Button(measurements_frame, text="Add Measurement", command=self.add_measurement).pack(fill="x", padx=5, pady=2)
        ttk.Button(measurements_frame, text="Clear Measurements", command=self.clear_measurements).pack(fill="x", padx=5, pady=2)
    
    def create_middle_panel_content(self):
        # Upper section for zoomed view
        self.upper_frame = ttk.Frame(self.middle_frame)
        self.upper_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create a figure for the zoomed view
        self.zoom_fig = Figure(figsize=(5, 3), dpi=100)
        self.zoom_ax = self.zoom_fig.add_subplot(111)
        self.zoom_canvas = FigureCanvasTkAgg(self.zoom_fig, master=self.upper_frame)
        self.zoom_canvas.draw()
        self.zoom_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Lower section for full image view
        self.lower_frame = ttk.Frame(self.middle_frame)
        self.lower_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create a figure for the full image
        self.main_fig = Figure(figsize=(5, 4), dpi=100)
        self.main_ax = self.main_fig.add_subplot(111)
        self.main_canvas = FigureCanvasTkAgg(self.main_fig, master=self.lower_frame)
        self.main_canvas.draw()
        self.main_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.main_canvas, self.lower_frame)
        self.toolbar.update()
        self.toolbar.pack(fill="x")
    
    def update_magnification_range(self):
        """Update the magnification slider range based on loaded image dimensions"""
        if self.displayed_image is None:
            return
        
        height, width = self.displayed_image.shape[:2]
        smallest_dim = min(height, width)
        
        # Maximum magnification: 10x10 pixels (so mag = 5 gives 11x11 region)
        self.max_magnification = 5
        
        # Minimum magnification: 10% of smallest dimension
        self.min_magnification = int(smallest_dim * 0.1 / 2)
        
        # Update slider configuration
        self.magnifier_slider.configure(from_=self.max_magnification, to=self.min_magnification)
        
        # Set initial value
        initial_mag = min(max(self.magnification, self.max_magnification), self.min_magnification)
        self.magnifier_var.set(initial_mag)
        self.magnification = int(initial_mag)
        
        # Update label
        self.update_magnification_label()
    
    def update_magnification_label(self):
        """Update the magnification label to show pixel dimensions"""
        mag = int(self.magnifier_var.get())
        pixel_size = 2 * mag + 1
        self.magnifier_label_var.set(f"Magnifier: {pixel_size} x {pixel_size} pixels")
    
    def save_project(self):
        if not self.extracted_data and not self.axes:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".fgd",
            filetypes=[("Figure Digitizer Project", "*.fgd"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
    
        if file_path:
            try:
                # Prepare project data
                project_data = {
                    'version': '1.0',
                    'image_path': self.image_path,
                    'axes': self.axes,
                    'extracted_data': {}
                }
            
                # Convert extracted data to serializable format
                for dataset_name, dataset in self.extracted_data.items():
                    project_data['extracted_data'][dataset_name] = {
                        'color': dataset['color'],
                        'points': dataset['points']
                    }
            
                # Save the project data
                with open(file_path, 'w') as f:
                    json.dump(project_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Project saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")

    def load_project(self):
        file_path = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("Figure Digitizer Project", "*.fgd"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
    
        if file_path:
            try:
                # Load the project data
                with open(file_path, 'r') as f:
                    project_data = json.load(f)
            
                # Check if the image path exists
                image_path = project_data.get('image_path', '')
                if not os.path.exists(image_path):
                    new_path = filedialog.askopenfilename(
                        title="Select Image File",
                        initialdir=os.path.dirname(image_path),
                        initialfile=os.path.basename(image_path),
                        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"), ("All files", "*.*")]
                    )
                    if new_path:
                        image_path = new_path
                    else:
                        return
            
                # Load the image
                self.image_path = image_path
                self.original_image = cv2.imread(image_path)
            
                # Convert BGR to RGB for display
                if self.original_image.shape[2] == 3:
                    self.original_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
            
                self.displayed_image = self.original_image.copy()
            
                # Update filename display
                filename = os.path.basename(image_path)
                directory = os.path.dirname(image_path)
                self.filename_var.set(f"{filename}\nDirectory: {directory}")
            
                # Load axes
                self.axes = project_data.get('axes', {})
            
                # Update axes listbox
                self.axes_listbox.delete(0, tk.END)
                for axes_name in self.axes:
                    self.axes_listbox.insert(tk.END, axes_name)
            
                # Load extracted data
                self.extracted_data = {}
                for dataset_name, dataset in project_data.get('extracted_data', {}).items():
                    self.extracted_data[dataset_name] = {
                        'color': dataset.get('color', self.get_random_color()),
                        'points': dataset.get('points', [])
                    }
            
                # Update data listbox
                self.data_listbox.delete(0, tk.END)
                for dataset_name in self.extracted_data:
                    self.data_listbox.insert(tk.END, dataset_name)
            
                # Update magnification range
                self.update_magnification_range()
            
                # Display the image
                self.display_image()
            
                # Show image settings in right panel
                self.show_image_settings_context()
            
                # Show the data overlay
                self.show_data_overlayed()
            
                messagebox.showinfo("Success", "Project loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {str(e)}")
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"), ("All files", "*.*")]
        )
    
        if file_path:
            try:
                # Load the image using OpenCV
                self.image_path = file_path
                self.original_image = cv2.imread(file_path)
            
                # Convert BGR to RGB for display
                if self.original_image.shape[2] == 3:
                    self.original_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
            
                self.displayed_image = self.original_image.copy()
            
                # Update filename display
                filename = os.path.basename(file_path)
                directory = os.path.dirname(file_path)
                self.filename_var.set(f"{filename}\nDirectory: {directory}")
            
                # Update magnification range based on image size
                self.update_magnification_range()
            
                # Display the image
                self.display_image()
            
                # Show image settings in right panel
                self.show_image_settings_context()
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def display_image(self):
        if self.displayed_image is None:
            return
        
        # Clear the main axes
        self.main_ax.clear()
    
        # Display the image
        self.main_ax.imshow(self.displayed_image, aspect='auto')
    
        # Remove ticks
        self.main_ax.set_xticks([])
        self.main_ax.set_yticks([])
    
        # Draw the canvas
        self.main_canvas.draw()
        
    def save_image(self):
        if self.displayed_image is None:
            messagebox.showwarning("Warning", "No image to save")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
    
        if file_path:
            try:
                # Convert RGB to BGR for OpenCV
                if len(self.displayed_image.shape) == 3 and self.displayed_image.shape[2] == 3:
                    save_image = cv2.cvtColor(self.displayed_image, cv2.COLOR_RGB2BGR)
                else:
                    save_image = self.displayed_image

                cv2.imwrite(file_path, save_image)
                messagebox.showinfo("Success", f"Image saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
        
    def bind_events(self):
        # Bind mouse events for the main canvas
        self.main_canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.main_canvas.mpl_connect('button_press_event', self.on_mouse_click)
        
    def on_mouse_move(self, event):
        if event.inaxes != self.main_ax:
            return
            
        # Update the zoomed view
        if self.displayed_image is not None:
            x, y = int(event.xdata), int(event.ydata)
            self.update_zoom_view(x, y)
    
    def on_mouse_click(self, event):
        if event.inaxes != self.main_ax or self.extraction_mode is None:
            return
            
        x, y = int(event.xdata), int(event.ydata)
        
        if self.current_dataset is None:
            # Create a new dataset if none is selected
            dataset_name = f"Dataset_{len(self.extracted_data) + 1}"
            self.extracted_data[dataset_name] = {'points': [], 'color': self.get_random_color()}
            self.current_dataset = dataset_name
            self.data_listbox.insert(tk.END, dataset_name)
            self.data_listbox.selection_clear(0, tk.END)
            self.data_listbox.selection_set(tk.END)
        
        if self.extraction_mode == 'add':
            # Add a point to the current dataset
            if self.current_axes and len(self.axes[self.current_axes]) > 0:
                # Convert pixel coordinates to data coordinates using the current axes
                data_x, data_y = self.pixel_to_data_coords(x, y)
                self.extracted_data[self.current_dataset]['points'].append((data_x, data_y, x, y))
                self.show_data_overlayed()
                
        elif self.extraction_mode == 'adjust':
            # Find the closest point and adjust it
            if self.current_dataset and len(self.extracted_data[self.current_dataset]['points']) > 0:
                closest_idx, min_dist = self.find_closest_point(x, y)
                if min_dist < 20:  # Only adjust if within a reasonable distance
                    # Update the point's position
                    data_x, data_y = self.pixel_to_data_coords(x, y)
                    self.extracted_data[self.current_dataset]['points'][closest_idx] = (data_x, data_y, x, y)
                    self.show_data_overlayed()
                
        elif self.extraction_mode == 'delete':
            # Find the closest point and delete it
            if self.current_dataset and len(self.extracted_data[self.current_dataset]['points']) > 0:
                closest_idx, min_dist = self.find_closest_point(x, y)
                if min_dist < 20:  # Only delete if within a reasonable distance
                    del self.extracted_data[self.current_dataset]['points'][closest_idx]
                    self.show_data_overlayed()
    
    def on_data_select(self, event):
        selection = self.data_listbox.curselection()
        if selection:
            self.current_dataset = self.data_listbox.get(selection[0])
                    
    def find_closest_point(self, x, y):
        points = self.extracted_data[self.current_dataset]['points']
        if not points:
            return None, float('inf')
            
        distances = [(i, np.sqrt((p[2] - x)**2 + (p[3] - y)**2)) for i, p in enumerate(points)]
        closest_idx, min_dist = min(distances, key=lambda d: d[1])
        return closest_idx, min_dist
    
    def update_zoom_view(self, x, y):
        if self.displayed_image is None:
            return
            
        # Clear the previous zoom view
        self.zoom_ax.clear()
        
        # Calculate the region to zoom in on
        mag = int(self.magnifier_var.get())
        height, width = self.displayed_image.shape[:2]
        
        # Ensure the region is within the image boundaries
        x_min = max(0, x - mag)
        x_max = min(width, x + mag + 1)
        y_min = max(0, y - mag)
        y_max = min(height, y + mag + 1)
        
        # Extract the region and display it
        if len(self.displayed_image.shape) == 3:  # Color image
            zoom_region = self.displayed_image[y_min:y_max, x_min:x_max, :]
        else:  # Grayscale image
            zoom_region = self.displayed_image[y_min:y_max, x_min:x_max]
            
        self.zoom_ax.imshow(zoom_region, aspect='auto')
        
        # Draw crosshair at the center
        center_x = x - x_min
        center_y = y - y_min
        self.zoom_ax.axhline(y=center_y, color=self.crosshair_color, linestyle='-', linewidth=1)
        self.zoom_ax.axvline(x=center_x, color=self.crosshair_color, linestyle='-', linewidth=1)
        
        # Remove ticks
        self.zoom_ax.set_xticks([])
        self.zoom_ax.set_yticks([])
        
        # Add coordinates text
        if self.current_axes and len(self.axes[self.current_axes]) > 0:
            data_x, data_y = self.pixel_to_data_coords(x, y)
            self.zoom_ax.set_title(f"X: {data_x:.2f}, Y: {data_y:.2f} (Px: {x}, {y})")
        else:
            self.zoom_ax.set_title(f"Px: {x}, {y}")
        
        self.zoom_canvas.draw()
    
    def pixel_to_data_coords(self, x, y):
        """Convert pixel coordinates to data coordinates using the current axes calibration"""
        if not self.current_axes or self.current_axes not in self.axes:
            return x, y
            
        axes_info = self.axes[self.current_axes]
        
        # Check if we have X and Y axes defined
        if 'X' in axes_info and 'Y' in axes_info:
            x_info = axes_info['X']
            y_info = axes_info['Y']
            
            # Linear interpolation between calibration points
            x_pixel = [x_info['lower_pixel'], x_info['upper_pixel']]
            x_value = [x_info['lower_value'], x_info['upper_value']]
            
            y_pixel = [y_info['lower_pixel'], y_info['upper_pixel']]
            y_value = [y_info['lower_value'], y_info['upper_value']]
            
            # Convert pixel to data value
            data_x = np.interp(x, x_pixel, x_value)
            data_y = np.interp(y, y_pixel, y_value)
            
            return data_x, data_y
        
        return x, y
    
    def data_to_pixel_coords(self, data_x, data_y):
        """Convert data coordinates to pixel coordinates using the current axes calibration"""
        if not self.current_axes or self.current_axes not in self.axes:
            return data_x, data_y
            
        axes_info = self.axes[self.current_axes]
        
        # Check if we have X and Y axes defined
        if 'X' in axes_info and 'Y' in axes_info:
            x_info = axes_info['X']
            y_info = axes_info['Y']
            
            # Linear interpolation between calibration points
            x_pixel = [x_info['lower_pixel'], x_info['upper_pixel']]
            x_value = [x_info['lower_value'], x_info['upper_value']]
            
            y_pixel = [y_info['lower_pixel'], y_info['upper_pixel']]
            y_value = [y_info['lower_value'], y_info['upper_value']]
            
            # Convert data value to pixel
            pixel_x = np.interp(data_x, x_value, x_pixel)
            pixel_y = np.interp(data_y, y_value, y_pixel)
            
            return pixel_x, pixel_y
        
        return data_x, data_y
    
    def save_data_single_csv(self):
        if not self.extracted_data:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
    
        if file_path:
            try:
                # Create a DataFrame with all datasets
                data_dict = {}
            
                for dataset_name, dataset in self.extracted_data.items():
                    if dataset['points']:
                        data_dict[f"{dataset_name}_x"] = [p[0] for p in dataset['points']]
                        data_dict[f"{dataset_name}_y"] = [p[1] for p in dataset['points']]
            
                df = pd.DataFrame(data_dict)
                df.to_csv(file_path, index=False)
            
                messagebox.showinfo("Success", f"Data saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def save_data_individual_csv(self):
        if not self.extracted_data:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        folder_path = filedialog.askdirectory(title="Select Folder to Save CSV Files")
    
        if folder_path:
            try:
                saved_count = 0
            
                for dataset_name, dataset in self.extracted_data.items():
                    if dataset['points']:
                        file_path = os.path.join(folder_path, f"{dataset_name}.csv")
                    
                        # Create a DataFrame for this dataset
                        df = pd.DataFrame({
                            'x': [p[0] for p in dataset['points']],
                            'y': [p[1] for p in dataset['points']]
                        })
                    
                        df.to_csv(file_path, index=False)
                        saved_count += 1
            
                if saved_count > 0:
                    messagebox.showinfo("Success", f"{saved_count} dataset(s) saved successfully to {folder_path}")
                else:
                    messagebox.showwarning("Warning", "No datasets were saved")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def show_image_settings_context(self):
        # Clear the right panel
        for widget in self.right_scrollable_frame.winfo_children():
            widget.destroy()
            
        # If no image is loaded, show a message
        if self.displayed_image is None:
            ttk.Label(self.right_scrollable_frame, text="No image loaded").pack(padx=5, pady=20)
            return
            
        # Create the Image Settings context view
        settings_frame = ttk.LabelFrame(self.right_scrollable_frame, text="Image Settings")
        settings_frame.pack(fill="x", padx=5, pady=5, expand=True)
        
        # Display image size
        height, width = self.displayed_image.shape[:2]
        ttk.Label(settings_frame, text=f"Image size: {width} x {height} pixels").pack(padx=5, pady=5)
        
        # Brightness slider
        brightness_frame = ttk.Frame(settings_frame)
        brightness_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(brightness_frame, text="Image brightness:").pack(side="left")
        brightness_slider = ttk.Scale(brightness_frame, from_=0.1, to=3.0, orient="horizontal", value=1.0)
        brightness_slider.pack(side="left", fill="x", expand=True, padx=5)
        brightness_slider.bind("<ButtonRelease-1>", lambda e: self.adjust_image_brightness(brightness_slider.get()))
        
        # Contrast slider
        contrast_frame = ttk.Frame(settings_frame)
        contrast_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(contrast_frame, text="Image contrast:").pack(side="left")
        contrast_slider = ttk.Scale(contrast_frame, from_=0.1, to=3.0, orient="horizontal", value=1.0)
        contrast_slider.pack(side="left", fill="x", expand=True, padx=5)
        contrast_slider.bind("<ButtonRelease-1>", lambda e: self.adjust_image_contrast(contrast_slider.get()))
        
        # Image manipulation buttons
        buttons_frame = ttk.Frame(settings_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Crop image", command=self.crop_image).pack(fill="x", padx=5, pady=2)
        ttk.Button(buttons_frame, text="Adjust contrast", command=self.auto_adjust_contrast).pack(fill="x", padx=5, pady=2)
        ttk.Button(buttons_frame, text="Undo image changes", command=self.reset_image).pack(fill="x", padx=5, pady=2)
        ttk.Button(buttons_frame, text="Save image", command=self.save_image).pack(fill="x", padx=5, pady=2)
    
    def show_axes_settings_context(self):
        # Clear the right panel
        for widget in self.right_scrollable_frame.winfo_children():
            widget.destroy()
            
        # If no axes is selected, show a message
        if not self.current_axes:
            ttk.Label(self.right_scrollable_frame, text="No axes selected").pack(padx=5, pady=20)
            return
            
        # Create the Axes Settings context view
        settings_frame = ttk.LabelFrame(self.right_scrollable_frame, text="Axes Settings")
        settings_frame.pack(fill="x", padx=5, pady=5, expand=True)
        
        # Display axes name
        ttk.Label(settings_frame, text=f"Axes: {self.current_axes}").pack(padx=5, pady=5)
        
        # Calibration points section
        calib_frame = ttk.LabelFrame(settings_frame, text="Calibration points")
        calib_frame.pack(fill="x", padx=5, pady=5)
        
        # Create header row
        header_frame = ttk.Frame(calib_frame)
        header_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(header_frame, text="Axis", width=10).grid(row=0, column=0, padx=2)
        ttk.Label(header_frame, text="Lower reference", width=20).grid(row=0, column=1, padx=2)
        ttk.Label(header_frame, text="Upper reference", width=20).grid(row=0, column=2, padx=2)
        
        # Get the axes info
        axes_info = self.axes.get(self.current_axes, {})
        
        # Create a row for each axis (X, Y, Z for ternary, etc.)
        row = 1
        for axis_name in ['X', 'Y', 'Z']:
            if axis_name in axes_info:
                axis_info = axes_info[axis_name]
                
                axis_frame = ttk.Frame(calib_frame)
                axis_frame.pack(fill="x", padx=5, pady=2)
                
                ttk.Label(axis_frame, text=axis_name, width=10).grid(row=0, column=0, padx=2)
                
                # Lower reference
                lower_frame = ttk.Frame(axis_frame)
                lower_frame.grid(row=0, column=1, padx=2)
                
                ttk.Label(lower_frame, text="Px:").pack(side="left")
                lower_px_var = tk.StringVar(value=str(axis_info.get('lower_pixel', 0)))
                lower_px_entry = ttk.Entry(lower_frame, textvariable=lower_px_var, width=5)
                lower_px_entry.pack(side="left", padx=2)
                
                ttk.Label(lower_frame, text="Val:").pack(side="left")
                lower_val_var = tk.StringVar(value=str(axis_info.get('lower_value', 0)))
                lower_val_entry = ttk.Entry(lower_frame, textvariable=lower_val_var, width=8)
                lower_val_entry.pack(side="left", padx=2)
                
                # Upper reference
                upper_frame = ttk.Frame(axis_frame)
                upper_frame.grid(row=0, column=2, padx=2)
                
                ttk.Label(upper_frame, text="Px:").pack(side="left")
                upper_px_var = tk.StringVar(value=str(axis_info.get('upper_pixel', 100)))
                upper_px_entry = ttk.Entry(upper_frame, textvariable=upper_px_var, width=5)
                upper_px_entry.pack(side="left", padx=2)
                
                ttk.Label(upper_frame, text="Val:").pack(side="left")
                upper_val_var = tk.StringVar(value=str(axis_info.get('upper_value', 100)))
                upper_val_entry = ttk.Entry(upper_frame, textvariable=upper_val_var, width=8)
                upper_val_entry.pack(side="left", padx=2)
                
                # Bind update function to entries
                entries = [lower_px_entry, lower_val_entry, upper_px_entry, upper_val_entry]
                vars_dict = {
                    'axis': axis_name,
                    'lower_px': lower_px_var,
                    'lower_val': lower_val_var,
                    'upper_px': upper_px_var,
                    'upper_val': upper_val_var
                }
                
                for entry in entries:
                    entry.bind("<FocusOut>", lambda e, v=vars_dict: self.update_axis_calibration(v))
                    entry.bind("<Return>", lambda e, v=vars_dict: self.update_axis_calibration(v))
                
                row += 1
        
        # Add button to add a new axis if needed
        if len(axes_info) < 3:  # Limit to 3 axes (X, Y, Z)
            ttk.Button(calib_frame, text="Add Axis", command=self.add_axis_to_current).pack(padx=5, pady=5)
        
        # Add button to apply calibration
        ttk.Button(settings_frame, text="Apply Calibration", command=self.apply_calibration).pack(fill="x", padx=5, pady=5)
    
    def on_plot_type_change(self, event):
        selected_plot_type = self.plot_type_var.get()
    
        # Clear existing axes
        self.axes.clear()
        self.axes_listbox.delete(0, tk.END)
    
        # Set up default axes based on the selected plot type
        if selected_plot_type == 'XY Plot':
            self.axes['XY'] = {'X': {}, 'Y': {}}
            self.axes_listbox.insert(tk.END, 'XY')
        elif selected_plot_type == 'Ternary Diagram':
            self.axes['Ternary'] = {'X': {}, 'Y': {}, 'Z': {}}
            self.axes_listbox.insert(tk.END, 'Ternary')
        elif selected_plot_type == 'Polar Plot':
            self.axes['Polar'] = {'R': {}, 'Theta': {}}
            self.axes_listbox.insert(tk.END, 'Polar')
        else:
            # For other plot types, you may need to define appropriate axes
            pass
    
        # Update the current axes
        if self.axes:
            self.current_axes = next(iter(self.axes))
        else:
            self.current_axes = None
    
        # Update the axes settings context
        self.show_axes_settings_context()
    
        # You may want to clear or update other related data
        self.extracted_data.clear()
        self.data_listbox.delete(0, tk.END)
    
        # Redraw the plot if necessary
        self.display_image()
        
    def show_extraction_settings_context(self):
        # Clear the right panel
        for widget in self.right_scrollable_frame.winfo_children():
            widget.destroy()
            
        # Create the Extraction Settings context view
        settings_frame = ttk.LabelFrame(self.right_scrollable_frame, text="Extraction Settings")
        settings_frame.pack(fill="x", padx=5, pady=5, expand=True)
        
        # Manual Extraction subsection
        manual_frame = ttk.LabelFrame(settings_frame, text="Manual Extraction")
        manual_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(manual_frame, text="Add point", command=self.set_add_point_mode).pack(fill="x", padx=5, pady=2)
        ttk.Button(manual_frame, text="Adjust point", command=self.set_adjust_point_mode).pack(fill="x", padx=5, pady=2)
        ttk.Button(manual_frame, text="Delete point", command=self.set_delete_point_mode).pack(fill="x", padx=5, pady=2)
        
        # Automatic Extraction subsection
        auto_frame = ttk.LabelFrame(settings_frame, text="Automatic Extraction")
        auto_frame.pack(fill="x", padx=5, pady=5)
        
        # Create notebook for tabs
        tab_control = ttk.Notebook(auto_frame)
        
        # Box tab
        box_tab = ttk.Frame(tab_control)
        tab_control.add(box_tab, text='Box')
        self.create_extraction_tab_content(box_tab, "Box")
        
        # Brush tab
        brush_tab = ttk.Frame(tab_control)
        tab_control.add(brush_tab, text='Brush')
        self.create_extraction_tab_content(brush_tab, "Brush")
        
        # Eraser tab
        eraser_tab = ttk.Frame(tab_control)
        tab_control.add(eraser_tab, text='Eraser')
        self.create_extraction_tab_content(eraser_tab, "Eraser")
        
        # View tab
        view_tab = ttk.Frame(tab_control)
        tab_control.add(view_tab, text='View')
        ttk.Button(view_tab, text="Show extraction regions", command=self.show_extraction_regions).pack(fill="x", padx=5, pady=5)
        ttk.Button(view_tab, text="Clear view", command=self.clear_extraction_view).pack(fill="x", padx=5, pady=5)
        
        tab_control.pack(expand=1, fill="both")
        
        # Dataset Settings subsection
        dataset_frame = ttk.LabelFrame(settings_frame, text="Dataset Settings")
        dataset_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(dataset_frame, text="Display Color", command=self.change_dataset_color).pack(fill="x", padx=5, pady=2)
        ttk.Button(dataset_frame, text="Rename Dataset", command=self.rename_dataset).pack(fill="x", padx=5, pady=2)
        ttk.Button(dataset_frame, text="Delete Dataset", command=self.delete_dataset).pack(fill="x", padx=5, pady=2)
        ttk.Button(dataset_frame, text="Edit Point Groups", command=self.edit_point_groups).pack(fill="x", padx=5, pady=2)
        ttk.Button(dataset_frame, text="View Data", command=self.view_dataset_data).pack(fill="x", padx=5, pady=2)
        ttk.Button(dataset_frame, text="Clear Data", command=self.clear_dataset_data).pack(fill="x", padx=5, pady=2)

    def create_extraction_tab_content(self, tab, tab_name):
        # Width section
        width_frame = ttk.Frame(tab)
        width_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(width_frame, text="Width:").pack(side="left")
        width_slider = ttk.Scale(width_frame, from_=1, to=50, orient="horizontal", value=self.brush_width)
        width_slider.pack(side="left", fill="x", expand=True, padx=5)
        width_slider.bind("<ButtonRelease-1>", lambda e: self.update_brush_width(width_slider.get()))
        
        ttk.Button(width_frame, text="Erase all", command=self.erase_all_extraction).pack(side="right", padx=5)
        
        # Color section
        color_frame = ttk.LabelFrame(tab, text="Color")
        color_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(color_frame, text="Select:").pack(side="left")
        color_var = tk.StringVar(value="Foreground")
        color_dropdown = ttk.Combobox(color_frame, textvariable=color_var, values=('Foreground', 'Background'))
        color_dropdown.pack(side="left", padx=5)
        color_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_current_color(color_var.get()))
        
        self.color_display = tk.Canvas(color_frame, width=30, height=30, bg=self.current_color)
        self.color_display.pack(side="left", padx=5)
        
        ttk.Button(color_frame, text="Choose Color", command=self.choose_extraction_color).pack(side="left", padx=5)
        
        # Algorithm section
        algo_frame = ttk.LabelFrame(tab, text="Algorithm")
        algo_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(algo_frame, text="Method:").pack(side="left")
        algo_var = tk.StringVar(value=self.current_algorithm)
        algo_dropdown = ttk.Combobox(algo_frame, textvariable=algo_var, 
                                     values=('Averaging Window', 'X-step w/ Interp.', 'X-step', 'Blob detector', 'Histogram'))
        algo_dropdown.pack(side="left", padx=5, fill="x", expand=True)
        algo_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_algorithm(algo_var.get()))
        
        # Delta X and Y inputs
        for delta in ['X', 'Y']:
            delta_frame = ttk.Frame(algo_frame)
            delta_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(delta_frame, text=f"delta {delta}:").pack(side="left")
            delta_var = tk.StringVar(value=str(getattr(self, f'delta_{delta.lower()}')))
            delta_spinbox = ttk.Spinbox(delta_frame, from_=1, to=100, textvariable=delta_var, width=5)
            delta_spinbox.pack(side="left", padx=5)
            delta_spinbox.bind("<FocusOut>", lambda e, d=delta.lower(): setattr(self, f'delta_{d}', int(delta_var.get())))
            ttk.Label(delta_frame, text="Px").pack(side="left")
        
        ttk.Button(algo_frame, text="Run", command=lambda: self.run_extraction_algorithm(tab_name)).pack(fill="x", padx=5, pady=5)

    def get_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def show_data_overlayed(self):
        if self.displayed_image is None or not self.extracted_data:
            return
        
        # Clear previous overlays
        self.main_ax.clear()
        self.main_ax.imshow(self.displayed_image, aspect='auto')
        
        for dataset_name, dataset in self.extracted_data.items():
            if dataset['points']:
                x_values = [p[0] for p in dataset['points']]
                y_values = [p[1] for p in dataset['points']]
                pixel_x, pixel_y = zip(*[self.data_to_pixel_coords(x, y) for x, y in zip(x_values, y_values)])
                self.main_ax.scatter(pixel_x, pixel_y, c=dataset['color'], label=dataset_name)
        
        self.main_ax.legend()
        self.main_canvas.draw()

    def change_crosshair_color(self):
        color = colorchooser.askcolor(initialcolor=self.crosshair_color)
        if color[1]:
            self.crosshair_color = color[1]
            # Update the zoom view to show the new crosshair color
            if hasattr(self, 'zoom_ax') and self.displayed_image is not None:
                self.update_zoom_view(int(self.main_ax.get_xlim()[1]/2), int(self.main_ax.get_ylim()[1]/2))

    def update_magnification(self, value=None):
        """Update magnification from slider and refresh zoom view"""
        try:
            self.magnification = int(self.magnifier_var.get())
            # Update the label
            self.update_magnification_label()
            # Update the zoom view with the new magnification
            if self.displayed_image is not None and hasattr(self, 'main_ax'):
                xlim = self.main_ax.get_xlim()
                ylim = self.main_ax.get_ylim()
                if xlim and ylim:
                    self.update_zoom_view(int(xlim[1]/2), int(ylim[1]/2))
        except (ValueError, AttributeError):
            pass

    def on_axes_select(self, event):
        selection = self.axes_listbox.curselection()
        if selection:
            self.current_axes = self.axes_listbox.get(selection[0])
            self.show_axes_settings_context()

    def add_axes(self):
        # Create a dialog to get the axes name
        axes_name = simpledialog.askstring("Add Axes", "Enter axes name:")
        if axes_name and axes_name not in self.axes:
            self.axes[axes_name] = {'X': {}, 'Y': {}}
            self.axes_listbox.insert(tk.END, axes_name)
            self.current_axes = axes_name
            self.show_axes_settings_context()

    def change_axes(self):
        if not self.current_axes:
            messagebox.showwarning("Warning", "No axes selected")
            return
    
        # Create a dialog to get the new axes name
        new_name = simpledialog.askstring("Change Axes", "Enter new axes name:", initialvalue=self.current_axes)
        if new_name and new_name != self.current_axes:
            # Copy axes data to new name
            self.axes[new_name] = self.axes[self.current_axes]
            # Delete old axes
            del self.axes[self.current_axes]
            # Update listbox
            self.axes_listbox.delete(0, tk.END)
            for axes_name in self.axes:
                self.axes_listbox.insert(tk.END, axes_name)
            # Update current axes
            self.current_axes = new_name
            self.show_axes_settings_context()

    def clear_axes(self):
        if not self.current_axes:
            messagebox.showwarning("Warning", "No axes selected")
            return
    
        if messagebox.askyesno("Confirm", f"Are you sure you want to clear the axes '{self.current_axes}'?"):
            del self.axes[self.current_axes]
            self.axes_listbox.delete(self.axes_listbox.curselection())
            if self.axes:
                self.current_axes = next(iter(self.axes))
            else:
                self.current_axes = None
            self.show_axes_settings_context()

    def clear_all_axes(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all axes?"):
            self.axes.clear()
            self.axes_listbox.delete(0, tk.END)
            self.current_axes = None
            self.show_axes_settings_context()

    def add_axis_to_current(self):
        if not self.current_axes:
            messagebox.showwarning("Warning", "No axes selected")
            return
    
        # Create a dialog to get the axis name
        axis_name = simpledialog.askstring("Add Axis", "Enter axis name (X, Y, Z, etc.):")
        if axis_name and axis_name not in self.axes[self.current_axes]:
            self.axes[self.current_axes][axis_name] = {}
            self.show_axes_settings_context()

    def update_axis_calibration(self, vars_dict):
        if not self.current_axes:
            return
    
        try:
            axis = vars_dict['axis']
            lower_px = int(vars_dict['lower_px'].get())
            lower_val = float(vars_dict['lower_val'].get())
            upper_px = int(vars_dict['upper_px'].get())
            upper_val = float(vars_dict['upper_val'].get())
        
            self.axes[self.current_axes][axis] = {
                'lower_pixel': lower_px,
                'lower_value': lower_val,
                'upper_pixel': upper_px,
                'upper_value': upper_val
            }
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Invalid calibration value: {str(e)}")

    def apply_calibration(self):
        if not self.current_axes:
            messagebox.showwarning("Warning", "No axes selected")
            return
    
        messagebox.showinfo("Success", "Calibration applied successfully")
        self.show_data_overlayed()

    def set_add_point_mode(self):
        self.extraction_mode = 'add'
        messagebox.showinfo("Mode", "Add point mode activated")

    def set_adjust_point_mode(self):
        self.extraction_mode = 'adjust'
        messagebox.showinfo("Mode", "Adjust point mode activated")

    def set_delete_point_mode(self):
        self.extraction_mode = 'delete'
        messagebox.showinfo("Mode", "Delete point mode activated")

    def update_brush_width(self, width):
        self.brush_width = int(width)

    def update_current_color(self, color_type):
        if color_type == 'Foreground':
            self.current_color = self.foreground_color
        else:
            self.current_color = self.background_color
        self.color_display.config(bg=self.current_color)

    def adjust_image_brightness(self, value):
        if self.original_image is None:
            return
    
        # Create a PIL image from the numpy array
        pil_image = Image.fromarray(self.original_image)
    
        # Apply brightness adjustment
        enhancer = ImageEnhance.Brightness(pil_image)
        adjusted_image = enhancer.enhance(value)
    
        # Convert back to numpy array
        self.displayed_image = np.array(adjusted_image)
    
        # Update the display
        self.display_image()

    def adjust_image_contrast(self, value):
        if self.original_image is None:
            return
    
        # Create a PIL image from the numpy array
        pil_image = Image.fromarray(self.original_image)
    
        # Apply contrast adjustment
        enhancer = ImageEnhance.Contrast(pil_image)
        adjusted_image = enhancer.enhance(value)
    
        # Convert back to numpy array
        self.displayed_image = np.array(adjusted_image)
    
        # Update the display
        self.display_image()

    def auto_adjust_contrast(self):
        if self.original_image is None:
            return
    
        # Convert to grayscale if it's a color image
        if len(self.original_image.shape) == 3:
            gray = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
        else:
            gray = self.original_image.copy()
    
        # Apply histogram equalization
        equalized = cv2.equalizeHist(gray)
    
        # If original was color, convert back to color
        if len(self.original_image.shape) == 3:
            self.displayed_image = cv2.cvtColor(equalized, cv2.COLOR_GRAY2RGB)
        else:
            self.displayed_image = equalized
    
        # Update the display
        self.display_image()

    def reset_image(self):
        if self.original_image is None:
            return
    
        self.displayed_image = self.original_image.copy()
        self.display_image()

    # Placeholder methods (to be implemented)
    def load_from_pdf(self):
        messagebox.showinfo("Info", "PDF loading functionality to be implemented")

    def link_project(self):
        messagebox.showinfo("Info", "Project linking functionality to be implemented")

    def display_data(self):
        messagebox.showinfo("Info", "Data display functionality to be implemented")

    def save_data(self):
        messagebox.showinfo("Info", "Data saving functionality to be implemented")

    def add_measurement(self):
        messagebox.showinfo("Info", "Measurement addition functionality to be implemented")

    def clear_measurements(self):
        messagebox.showinfo("Info", "Measurement clearing functionality to be implemented")

    def crop_image(self):
        messagebox.showinfo("Info", "Image cropping functionality to be implemented")

    def show_extraction_regions(self):
        messagebox.showinfo("Info", "Extraction regions display functionality to be implemented")

    def clear_extraction_view(self):
        messagebox.showinfo("Info", "Extraction view clearing functionality to be implemented")

    def change_dataset_color(self):
        messagebox.showinfo("Info", "Dataset color change functionality to be implemented")

    def rename_dataset(self):
        messagebox.showinfo("Info", "Dataset renaming functionality to be implemented")

    def delete_dataset(self):
        messagebox.showinfo("Info", "Dataset deletion functionality to be implemented")

    def edit_point_groups(self):
        messagebox.showinfo("Info", "Point group editing functionality to be implemented")

    def view_dataset_data(self):
        messagebox.showinfo("Info", "Dataset viewing functionality to be implemented")

    def clear_dataset_data(self):
        messagebox.showinfo("Info", "Dataset clearing functionality to be implemented")

    def erase_all_extraction(self):
        messagebox.showinfo("Info", "Extraction erasing functionality to be implemented")

    def choose_extraction_color(self):
        color = colorchooser.askcolor(initialcolor=self.current_color)
        if color[1]:
            self.current_color = color[1]
            self.color_display.config(bg=self.current_color)

    def update_algorithm(self, algorithm):
        self.current_algorithm = algorithm

    def run_extraction_algorithm(self, mode):
        messagebox.showinfo("Info", f"Running {self.current_algorithm} algorithm in {mode} mode")
        # Implement the actual algorithm here

if __name__ == "__main__":
    root = tk.Tk()
    app = Figure_Digitizer(root)
    root.mainloop()
