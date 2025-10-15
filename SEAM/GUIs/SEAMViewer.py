
"""
2025. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National 
Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of 
Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad 
National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. 
The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, 
irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute 
copies to the public, perform publicly and display publicly, and to permit others to do so.

@author: Aaron Pital (Los Alamos National Lab)
Created:  2024-04-19

Description: 


Notes:
    -
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import json
import math
from SEAM.GUIs.AnnotatePDF import PDFAnnotator
from SEAM.GUIs.AnnotateDefects import DefectAnnotator

blank_tree_dict = {
    'projects': [],
    
    }


class Landing_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SEAM Analysis Tool")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize dictionaries
        self.tree_view_dict = {}  # Dictionary for tree view
        self.selected_objects = {}  # Dictionary for selected items
        self.process_files = {}  # Dictionary for process files
        self.unsaved_changes = {}  # Dictionary for unsaved project changes
        
        # Initialize project root directory
        self.project_root_dir = str(Path.home())
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create panels
        self.create_panels()
        
        # Create left panel blocks
        self.create_left_panel_blocks()
        
        # Create middle panel tree view
        self.create_tree_view()
        
        # Create right panel canvas
        self.create_right_panel_canvas()
        
        # Set up event bindings
        self.setup_bindings()

    def create_menu_bar(self):
        menu_bar = tk.Menu(self.root)
        
        # SEAM Menu
        seam_menu = tk.Menu(menu_bar, tearoff=0)
        seam_menu.add_command(label="SEAM Root", command=self.set_seam_root)
        seam_menu.add_command(label="Load project", command=self.load_project)
        seam_menu.add_command(label="Save project", command=self.save_project)
        seam_menu.add_command(label="Load GROUP", command=self.load_group)
        seam_menu.add_command(label="Create GROUP", command=self.create_group)
        menu_bar.add_cascade(label="SEAM", menu=seam_menu)
        
        # Data Menu
        data_menu = tk.Menu(menu_bar, tearoff=0)
        data_menu.add_command(label="SEAM File Summary", command=self.file_summary)
        data_menu.add_command(label="SEAM Directory Summary", command=self.dir_summary)
        data_menu.add_command(label="Show Data Fingerprint", command=self.data_fingerprint)
        menu_bar.add_cascade(label="Data", menu=data_menu)
        
        # Analysis Menu
        analysis_menu = tk.Menu(menu_bar, tearoff=0)
        analysis_menu.add_command(label="Images", command=self.analyze_images)
        analysis_menu.add_command(label="Spectra", command=self.analyze_spectra)
        analysis_menu.add_command(label="Pressure", command=self.analyze_pressure)
        analysis_menu.add_command(label="Document", command=self.analyze_document)
        menu_bar.add_cascade(label="Analysis", menu=analysis_menu)
        
        # Recipes Menu
        recipes_menu = tk.Menu(menu_bar, tearoff=0)
        recipes_menu.add_command(label="View Recipe Tree", command=self.view_recipe_tree)
        recipes_menu.add_command(label="Modify Recipe", command=self.modify_recipe)
        recipes_menu.add_command(label="Test Recipe", command=self.test_recipe)
        menu_bar.add_cascade(label="Recipes", menu=recipes_menu)
        
        # Process Menu
        process_menu = tk.Menu(menu_bar, tearoff=0)
        process_menu.add_command(label="Process Directory", command=self.process_directory)
        process_menu.add_command(label="Load PROCESS", command=self.load_process)
        process_menu.add_command(label="Create PROCESS", command=self.create_process)
        process_menu.add_command(label="Link data by PROCESS", command=self.link_data_by_process)
        menu_bar.add_cascade(label="Process", menu=process_menu)
        
        # View Menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Nested Data View", command=self.nested_data_view)
        view_menu.add_command(label="View tree in separate window", command=self.tree_separate_window)
        view_menu.add_command(label="View", command=self.view_command)
        menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Graph Menu
        graph_menu = tk.Menu(menu_bar, tearoff=0)
        graph_menu.add_command(label="Open Graph View", command=self.open_graph_view)
        graph_menu.add_command(label="Graph Selected", command=self.graph_selected)
        menu_bar.add_cascade(label="Graph", menu=graph_menu)
        
        # Output Menu
        output_menu = tk.Menu(menu_bar, tearoff=0)
        output_menu.add_command(label="Export Results", command=self.export_results)
        output_menu.add_command(label="Create Report", command=self.print_report)
        menu_bar.add_cascade(label="Output", menu=output_menu)
        
        self.root.config(menu=menu_bar)

    def create_panels(self):
        # Create paned window for the three panels
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel
        self.left_panel = ttk.Frame(self.paned_window, width=250)
        self.paned_window.add(self.left_panel, weight=1)
        
        # Middle panel
        self.middle_panel = ttk.Frame(self.paned_window, width=400)
        self.paned_window.add(self.middle_panel, weight=2)
        
        # Right panel
        self.right_panel = ttk.Frame(self.paned_window, width=550)
        self.paned_window.add(self.right_panel, weight=3)

    def create_left_panel_blocks(self):
        # SEAM Block
        self.seam_frame = ttk.LabelFrame(self.left_panel, text="SEAM")
        self.seam_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.seam_frame, text="Select root", command=self.select_root).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self.seam_frame, text="Add mirror repo", command=self.add_mirror_repo).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self.seam_frame, text="Update Tree", command=self.update_tree).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(self.seam_frame, text="Root filepath:").pack(anchor=tk.W, padx=5, pady=2)
        self.root_filepath_var = tk.StringVar(value=self.project_root_dir)
        ttk.Entry(self.seam_frame, textvariable=self.root_filepath_var).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(self.seam_frame, text="Mirror repo filepath:").pack(anchor=tk.W, padx=5, pady=2)
        self.mirror_repo_var = tk.StringVar()
        ttk.Entry(self.seam_frame, textvariable=self.mirror_repo_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Analyze Block
        self.analyze_frame = ttk.LabelFrame(self.left_panel, text="Data Analysis")
        self.analyze_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.analyze_frame, text="Annotate PDF", command=self.open_annotate_pdf).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self.analyze_frame, text="Annotate Image (corrosion)", command=self.open_annotate_corrosion).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self.analyze_frame, text="Selection Analysis", command=self.open_analysis_window).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self.analyze_frame, text="Generate Report", command=self.generate_report).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self.analyze_frame, text="Open Analysis Window", command=self.load_analysis).pack(fill=tk.X, padx=5, pady=2)
        
        # Display Block
        self.display_frame = ttk.LabelFrame(self.left_panel, text="Display")
        self.display_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.display_frame, text="Expand right panel", command=self.expand_right_panel).pack(fill=tk.X, padx=5, pady=2)
        
        # Summarize Block
        self.summarize_frame = ttk.LabelFrame(self.left_panel, text="Summarize")
        self.summarize_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.summarize_frame, text="Summarize Data", command=self.summarize_data).pack(fill=tk.X, padx=5, pady=2)

    def create_tree_view(self):
        # Create a frame for the tree view
        tree_frame = ttk.Frame(self.middle_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Create the tree view
        self.tree = ttk.Treeview(tree_frame, selectmode='extended', 
                                yscrollcommand=y_scrollbar.set, 
                                xscrollcommand=x_scrollbar.set)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)
        
        # Place the tree and scrollbars
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure columns
        self.tree["columns"] = ("type", "size")
        self.tree.column("#0", width=200, minwidth=100)
        self.tree.column("type", width=100, minwidth=50)
        self.tree.column("size", width=100, minwidth=50)
        
        # Configure headings
        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.heading("type", text="Filetype", anchor=tk.W)
        self.tree.heading("size", text="Number of entries", anchor=tk.W)
        
        # Configure categories
        self.tree.insert("", "end", text="All SEAM contents", values=("Folder", ""), iid="all_seami", open=False)
        self.tree.insert("all_seami", "end", text="Project Files", values=("Folder", ""), iid="all_projects", open=False)
        self.tree.insert("all_seami", "end", text="GROUP Files", values=("Folder", ""), iid="all_groups", open=False)
        self.tree.insert("all_seami", "end", text="RECIPE Files", values=("Folder", ""), iid="all_recipes", open=False)
        self.tree.insert("all_seami", "end", text="SPECIFICATIONS Files", values=("Folder", ""), iid="all_specs", open=False)
        self.tree.insert("all_seami", "end", text="SEAM Results", values=("Folder", ""), iid="all_results", open=False)
        
        # Configure categories
        self.tree.insert("", "end", text="Current Project", values=("Folder", ""), iid="current_project", open=False)
        self.tree.insert("current_project", "end", text="GROUP Files", values=("Folder", ""), iid="current_groups", open=False)
        self.tree.insert("current_project", "end", text="SPEC Files", values=("Folder", ""), iid="current_processes", open=False)
        self.tree.insert("current_project", "end", text="RECIPE Files", values=("Folder", ""), iid="recipes", open=False)
        
        # Sample data
        # self.tree.insert("", "end", text="Sample Folder", values=("Folder", ""), iid="folder1", open=False)
        # self.tree.insert("folder1", "end", text="Sample File 1", values=("File", "10 KB"), iid="file1")
        # self.tree.insert("folder1", "end", text="Sample File 2", values=("File", "20 KB"), iid="file2")

    def create_right_panel_canvas(self):
        # Create a frame for the canvas
        canvas_frame = ttk.Frame(self.right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        x_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        
        # Create the canvas
        self.canvas = tk.Canvas(canvas_frame, bg="white", 
                               yscrollcommand=y_scrollbar.set, 
                               xscrollcommand=x_scrollbar.set)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.canvas.yview)
        x_scrollbar.config(command=self.canvas.xview)
        
        # Place the canvas and scrollbars
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas configuration variables
        self.canvas_objects = {}  # Dictionary to store canvas objects
        self.canvas_lines = {}  # Dictionary to store canvas lines
        self.canvas_scale = 1.0  # Current zoom level
        self.canvas_drag_data = {"x": 0, "y": 0, "item": None}  # Data for dragging items
        
        # Create toolbar for the right panel
        self.create_right_panel_toolbar()
        
        # Add sample shapes
        self.add_sample_shapes()

    def create_right_panel_toolbar(self):
        # Create a frame for the toolbar
        toolbar_frame = ttk.Frame(self.right_panel)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Line weight control
        ttk.Label(toolbar_frame, text="Line Weight:").pack(side=tk.LEFT, padx=2)
        self.line_weight_var = tk.StringVar(value="1")
        line_weight_combo = ttk.Combobox(toolbar_frame, textvariable=self.line_weight_var, 
                                         values=["1", "2", "3", "4", "5"], width=3)
        line_weight_combo.pack(side=tk.LEFT, padx=2)
        line_weight_combo.bind("<<ComboboxSelected>>", self.update_line_style)
        
        # Line color control
        ttk.Label(toolbar_frame, text="Line Color:").pack(side=tk.LEFT, padx=2)
        self.line_color_var = tk.StringVar(value="black")
        line_color_combo = ttk.Combobox(toolbar_frame, textvariable=self.line_color_var, 
                                       values=["black", "red", "blue", "green", "purple"], width=6)
        line_color_combo.pack(side=tk.LEFT, padx=2)
        line_color_combo.bind("<<ComboboxSelected>>", self.update_line_style)
        
        # Shape control
        ttk.Label(toolbar_frame, text="Shape:").pack(side=tk.LEFT, padx=2)
        self.shape_var = tk.StringVar(value="rectangle")
        shape_combo = ttk.Combobox(toolbar_frame, textvariable=self.shape_var, 
                                  values=["rectangle", "oval", "diamond"], width=8)
        shape_combo.pack(side=tk.LEFT, padx=2)
        shape_combo.bind("<<ComboboxSelected>>", self.update_shape_style)
        
        # Shape color control
        ttk.Label(toolbar_frame, text="Shape Color:").pack(side=tk.LEFT, padx=2)
        self.shape_color_var = tk.StringVar(value="lightblue")
        shape_color_combo = ttk.Combobox(toolbar_frame, textvariable=self.shape_color_var, 
                                        values=["lightblue", "lightgreen", "lightyellow", "pink", "lightgray"], width=8)
        shape_color_combo.pack(side=tk.LEFT, padx=2)
        shape_color_combo.bind("<<ComboboxSelected>>", self.update_shape_style)
        
        # Reset zoom button
        ttk.Button(toolbar_frame, text="Reset Zoom", command=self.reset_zoom).pack(side=tk.RIGHT, padx=2)

    def setup_bindings(self):
        # Tree view selection binding
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Canvas bindings for zooming and panning
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        self.canvas.bind("<ButtonPress-2>", self.on_canvas_pan_start)  # Middle button press
        self.canvas.bind("<B2-Motion>", self.on_canvas_pan)  # Middle button drag
        
        # Canvas bindings for item manipulation
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_item_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_item_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_item_release)

    def populate_tree_from_dict(self, tree_dict):
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Populate tree from dictionary
        def add_node(parent, key, value):
            if isinstance(value, dict):
                node = self.tree.insert(parent, "end", text=key, values=("Folder", ""))
                for k, v in value.items():
                    add_node(node, k, v)
            else:
                self.tree.insert(parent, "end", text=key, values=("File", value))
        
        for key, value in tree_dict.items():
            add_node("", key, value)

    def add_sample_shapes(self):
        # Add some sample shapes to the canvas
        shape1 = self.canvas.create_rectangle(50, 50, 150, 100, fill="lightblue", tags=("shape", "item1"))
        text1 = self.canvas.create_text(100, 75, text="Item 1", tags=("text", "item1"))
        
        shape2 = self.canvas.create_rectangle(250, 150, 350, 200, fill="lightgreen", tags=("shape", "item2"))
        text2 = self.canvas.create_text(300, 175, text="Item 2", tags=("text", "item2"))
        
        shape3 = self.canvas.create_rectangle(150, 250, 250, 300, fill="lightyellow", tags=("shape", "item3"))
        text3 = self.canvas.create_text(200, 275, text="Item 3", tags=("text", "item3"))
        
        # Store shapes in dictionary
        self.canvas_objects["item1"] = {"shape": shape1, "text": text1}
        self.canvas_objects["item2"] = {"shape": shape2, "text": text2}
        self.canvas_objects["item3"] = {"shape": shape3, "text": text3}
        
        # Add connecting lines with splines
        line1 = self.canvas.create_line(
            100, 100, 150, 150, 200, 250,
            smooth=True, width=2, fill="black", tags=("line", "line1_2")
        )
        
        line2 = self.canvas.create_line(
            300, 200, 250, 225, 200, 250,
            smooth=True, width=2, fill="black", tags=("line", "line2_3")
        )
        
        # Store lines in dictionary
        self.canvas_lines["line1_2"] = {"line": line1, "from": "item1", "to": "item3"}
        self.canvas_lines["line2_3"] = {"line": line2, "from": "item2", "to": "item3"}

    def update_connecting_lines(self):
        # Update the position of all connecting lines based on the current position of shapes
        for line_id, line_data in self.canvas_lines.items():
            line = line_data["line"]
            from_item = line_data["from"]
            to_item = line_data["to"]
            
            # Get the coordinates of the connected shapes
            from_coords = self.get_shape_connection_point(from_item)
            to_coords = self.get_shape_connection_point(to_item)
            
            # Calculate a control point for the spline
            control_x = (from_coords[0] + to_coords[0]) / 2
            control_y = (from_coords[1] + to_coords[1]) / 2
            
            # Update the line coordinates
            self.canvas.coords(
                line, 
                from_coords[0], from_coords[1],
                control_x, control_y,
                to_coords[0], to_coords[1]
            )

    def get_shape_connection_point(self, item_id):
        # Get the center point of a shape for line connections
        if item_id in self.canvas_objects:
            shape = self.canvas_objects[item_id]["shape"]
            coords = self.canvas.coords(shape)
            
            # For rectangle: x1, y1, x2, y2
            if len(coords) == 4:
                center_x = (coords[0] + coords[2]) / 2
                center_y = (coords[1] + coords[3]) / 2
                return (center_x, center_y)
        
        # Default fallback
        return (0, 0)

    # Event handlers
    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        
        # Update selected_objects dictionary
        self.selected_objects.clear()
        for item in selected_items:
            item_text = self.tree.item(item, "text")
            item_values = self.tree.item(item, "values")
            self.selected_objects[item] = {"text": item_text, "values": item_values}
        
        # Update the canvas with the selected items
        self.update_canvas_with_selection()

    def update_canvas_with_selection(self):
        # This is a simplified version - in a real app, you would create
        # shapes based on the actual selected items
        pass

    def on_mouse_wheel(self, event):
        # Handle zoom with mouse wheel
        delta = 1.1  # Zoom factor
        
        # Determine the direction of zoom
        if event.num == 5 or event.delta < 0:  # Scroll down or Windows negative delta
            factor = 1.0 / delta
        else:  # Scroll up or Windows positive delta
            factor = delta
        
        # Get the current scale and apply the zoom factor
        self.canvas_scale *= factor
        
        # Limit the scale to reasonable bounds
        self.canvas_scale = max(0.1, min(self.canvas_scale, 5.0))
        
        # Apply the scaling to all canvas objects
        self.canvas.scale("all", 0, 0, factor, factor)
        
        # Update the canvas scrollregion
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_pan_start(self, event):
        # Start panning the canvas
        self.canvas.scan_mark(event.x, event.y)

    def on_canvas_pan(self, event):
        # Pan the canvas
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_canvas_item_click(self, event):
        # Handle click on canvas items
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tags = self.canvas.gettags(item)
            if "shape" in tags:
                # Find which item this shape belongs to
                for tag in tags:
                    if tag.startswith("item"):
                        self.canvas_drag_data["item"] = tag
                        self.canvas_drag_data["x"] = event.x
                        self.canvas_drag_data["y"] = event.y
                        break

    def on_canvas_item_drag(self, event):
        # Handle dragging canvas items
        if self.canvas_drag_data["item"]:
            # Calculate the movement delta
            dx = event.x - self.canvas_drag_data["x"]
            dy = event.y - self.canvas_drag_data["y"]
            
            # Move the shape and its text
            item_id = self.canvas_drag_data["item"]
            if item_id in self.canvas_objects:
                shape = self.canvas_objects[item_id]["shape"]
                text = self.canvas_objects[item_id]["text"]
                
                self.canvas.move(shape, dx, dy)
                self.canvas.move(text, dx, dy)
            
            # Update the stored position
            self.canvas_drag_data["x"] = event.x
            self.canvas_drag_data["y"] = event.y
            
            # Update connecting lines
            self.update_connecting_lines()

    def on_canvas_item_release(self, event):
        # Reset drag data when mouse is released
        self.canvas_drag_data = {"x": 0, "y": 0, "item": None}

    def update_line_style(self, event=None):
        # Update the style of all lines
        width = int(self.line_weight_var.get())
        color = self.line_color_var.get()
        
        for line_data in self.canvas_lines.values():
            self.canvas.itemconfig(line_data["line"], width=width, fill=color)

    def update_shape_style(self, event=None):
        # Update the style of all shapes
        shape_type = self.shape_var.get()
        color = self.shape_color_var.get()
        
        for item_id, item_data in self.canvas_objects.items():
            shape = item_data["shape"]
            
            # Update the color
            self.canvas.itemconfig(shape, fill=color)
            
            # If shape type has changed, we would need to recreate the shapes
            # This is a simplified version that just changes the color

    def reset_zoom(self):
        # Reset zoom to original scale
        factor = 1.0 / self.canvas_scale
        self.canvas_scale = 1.0
        
        # Apply the scaling to all canvas objects
        self.canvas.scale("all", 0, 0, factor, factor)
        
        # Update the canvas scrollregion
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # Menu command methods
    def set_seam_root(self):
        messagebox.showinfo("SEAM Root", "Set SEAM Root functionality")

    def open_annotate_pdf(self):
        annotator_window = tk.Toplevel(self.root)
        app = PDFAnnotator(annotator_window)
        annotator_window.mainloop()

    def open_annotate_corrosion(self):
        defect_window = tk.Toplevel(self.root)
        app = DefectAnnotator(defect_window)
        defect_window.mainloop()

    def load_project(self):
        file_path = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    project_data = json.load(file)
                    # Process project data
                    messagebox.showinfo("Success", f"Project loaded from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {str(e)}")

    def save_project(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Prepare project data
                project_data = {
                    "tree_view_dict": self.tree_view_dict,
                    "selected_objects": self.selected_objects,
                    "process_files": self.process_files,
                    "project_root_dir": self.project_root_dir
                }
                
                with open(file_path, 'w') as file:
                    json.dump(project_data, file, indent=2)
                    
                messagebox.showinfo("Success", f"Project saved to {file_path}")
                self.unsaved_changes = {}
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")

    def load_group(self):
        messagebox.showinfo("Load GROUP", "Load GROUP functionality")

    def create_group(self):
        messagebox.showinfo("Create GROUP", "Create GROUP functionality")

    def file_summary(self):
        messagebox.showinfo("SEAM File Summary", "SEAM File Summary functionality")

    def dir_summary(self):
        messagebox.showinfo("SEAM Directory Summary", "SEAM Directory Summary functionality")

    def data_fingerprint(self):
        messagebox.showinfo("Data Fingerprint", "Show Data Fingerprint functionality")

    def analyze_images(self):
        messagebox.showinfo("Analyze Images", "Analyze Images functionality")

    def analyze_spectra(self):
        messagebox.showinfo("Analyze Spectra", "Analyze Spectra functionality")

    def analyze_pressure(self):
        messagebox.showinfo("Analyze Pressure", "Analyze Pressure functionality")

    def analyze_document(self):
        messagebox.showinfo("Analyze Document", "Analyze Document functionality")

    def view_recipe_tree(self):
        messagebox.showinfo("View Recipe Tree", "View Recipe Tree functionality")

    def modify_recipe(self):
        messagebox.showinfo("Modify Recipe", "Modify Recipe functionality")

    def test_recipe(self):
        messagebox.showinfo("Test Recipe", "Test Recipe functionality")

    def process_directory(self):
        messagebox.showinfo("Process Directory", "Process Directory functionality")

    def load_process(self):
        messagebox.showinfo("Load PROCESS", "Load PROCESS functionality")

    def create_process(self):
        messagebox.showinfo("Create PROCESS", "Create PROCESS functionality")

    def link_data_by_process(self):
        messagebox.showinfo("Link Data by PROCESS", "Link Data by PROCESS functionality")

    def nested_data_view(self):
        messagebox.showinfo("Nested Data View", "Nested Data View functionality")

    def tree_separate_window(self):
        messagebox.showinfo("Tree in Separate Window", "View Tree in Separate Window functionality")

    def view_command(self):
        messagebox.showinfo("View", "View functionality")

    def open_graph_view(self):
        messagebox.showinfo("Open Graph View", "Open Graph View functionality")

    def graph_selected(self):
        messagebox.showinfo("Graph Selected", "Graph Selected functionality")

    def export_results(self):
        messagebox.showinfo("Export Results", "Export Results functionality")

    def print_report(self):
        messagebox.showinfo("Print Report", "Print Report functionality")

    # Left panel button methods
    def select_root(self):
        directory = filedialog.askdirectory(title="Select Root Directory")
        if directory:
            self.project_root_dir = directory
            self.root_filepath_var.set(directory)
            messagebox.showinfo("Root Selected", f"Selected root directory: {directory}")

    def add_mirror_repo(self):
        directory = filedialog.askdirectory(title="Select Mirror Repository")
        if directory:
            self.mirror_repo_var.set(directory)
            messagebox.showinfo("Mirror Repository", f"Added mirror repository: {directory}")

    def update_tree(self, tree_dict):
        
        if len(tree_dict)==0:
            # Sample tree view dictionary
            tree_dict = {
                "Project A": {
                    "Data": {
                        "file1.dat": "50 KB",
                        "file2.dat": "120 KB"
                    },
                    "Results": {
                        "analysis.txt": "10 KB",
                        "graph.png": "200 KB"
                    }
                },
                "Project B": {
                    "Raw Data": {
                        "scan001.dat": "1.2 MB",
                        "scan002.dat": "1.5 MB"
                    }
                }
            }
        
        # Update the tree view dictionary and populate the tree
        self.tree_view_dict = tree_dict
        self.populate_tree_from_dict(self.tree_view_dict)
        messagebox.showinfo("Tree Updated", "Tree view has been updated")

    def open_analysis_window(self):
        """
        Description: Take selected items from tree view, create a new analysis window, and populate with selection.
        """
        
        if not self.selected_objects:
            messagebox.showinfo("No Selection", "Please select items to analyze")
        else:
            messagebox.showinfo("Analyze", f"Analyzing {len(self.selected_objects)} selected items")

    def generate_report(self):
        messagebox.showinfo("Generate Report", "Generating report for selected items")

    def save_analysis(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Analysis",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("Save Analysis", f"Analysis saved to {file_path}")

    def load_analysis(self):
        file_path = filedialog.askopenfilename(
            title="Load Analysis",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("Load Analysis", f"Analysis loaded from {file_path}")

    def expand_right_panel(self):
        # Adjust the paned window to give more space to the right panel
        # Get current window width
        window_width = self.root.winfo_width()
        
        # Calculate new positions for the sashes
        first_sash_pos = int(window_width * 0.15)  # 15% for left panel
        second_sash_pos = int(window_width * 0.35)  # 20% for middle panel, 65% for right panel
        
        # Set the sash positions
        try:
            self.paned_window.sashpos(0, first_sash_pos)
            self.paned_window.sashpos(1, second_sash_pos)
            messagebox.showinfo("Expand Right Panel", "Right panel expanded")
        except Exception as e:
            # Alternative approach if sashpos doesn't work
            self.paned_window.forget(self.left_panel)
            self.paned_window.forget(self.middle_panel)
            self.paned_window.forget(self.right_panel)
            
            # Re-add with appropriate weights
            self.paned_window.add(self.left_panel, weight=1)
            self.paned_window.add(self.middle_panel, weight=2)
            self.paned_window.add(self.right_panel, weight=7)

    def summarize_data(self):
        messagebox.showinfo("Summarize Data", "Summarizing data")


# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = Landing_GUI(root)
    root.mainloop()

