# -*- coding: utf-8 -*-
"""
Created on Mon Sep 22 13:06:52 2025

@author: 359794
"""

import sys
import json
import fitz  # PyMuPDF
import numpy as np
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import io
import os

class PDFAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Annotator")
        self.root.geometry("1000x800")
        
        self.pdf_document = None
        self.current_page = 0
        self.zoom_factor = 1.0
        self.current_tool = "select"
        self.current_color = "#FF0000"  # Red with 50% opacity
        self.current_annotation_type = "General"
        self.annotation_color_dict = {
            "#F53C14": "Text, titles",
            "#F56E14": "Text, authors",
            "#F5C814": "Text, abstract",
            "#97F514": "Text, body",
            "#B57422": "Text, author info",
            "#14BA94": "Text, caption",
            "#2CA6DE": "Text, references",
            "#6725F7": "Figure",
            "#CD25F7": "Table",  
            "#DE2CD6": "Special-1",
            "#F725A3": "Special-2",
            "#F01D52": "Special-3",
            "#FF0000": "General"
            }
        self.current_color_alpha = 128  # Alpha value (0-255)
        self.polygons = {}  # Dictionary to store polygons by page: {page_num: [(polygon, color), ...]}
        self.current_polygon = []
        self.selected_polygon_index = -1
        self.polygon_dict = {}  # Dictionary to store polygons and their content
        self.used_colors = []  # Track colors that have been used
        
        # Variables for editing polygons
        self.editing_polygon = False
        self.editing_index = -1
        self.editing_points = None
        self.dragging_point = False
        self.dragging_point_index = -1
        
        # Variables for canvas panning
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        self.init_ui()
    
    def init_ui(self):
        # Create main layout
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create horizontal layout for controls (left) and PDF view (right)
        h_layout = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        h_layout.pack(fill=tk.BOTH, expand=True)
        
        # Create controls frame (left side)
        self.controls_frame = ttk.Frame(h_layout, width=200)
        h_layout.add(self.controls_frame, weight=1)
        
        # Create PDF view frame (right side)
        pdf_frame = ttk.Frame(h_layout)
        h_layout.add(pdf_frame, weight=4)
        
        # Add controls to left panel
        self.create_controls()
        
        # Create PDF view area with scroll bars
        self.scroll_frame = ttk.Frame(pdf_frame)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(self.scroll_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(self.scroll_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas for PDF display
        self.canvas = tk.Canvas(self.scroll_frame, 
                               xscrollcommand=self.h_scrollbar.set,
                               yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Button-2>", self.on_pan_start)  # Middle button
        self.canvas.bind("<B2-Motion>", self.on_pan_motion)
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        self.root.bind("<Escape>", self.on_escape)
        
        # Store the canvas image reference
        self.canvas_image_id = None
        self.canvas_image = None
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF", command=self.open_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Annotations menu
        annotations_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Annotations", menu=annotations_menu)
        annotations_menu.add_command(label="Save Annotations", command=self.save_annotations)
        annotations_menu.add_command(label="Load Annotations", command=self.load_annotations)
        annotations_menu.add_separator()
        annotations_menu.add_command(label="View Annotation Dictionary", command=self.show_annotation_dict)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Analyze Content", command=self.analyze_content)
    
    def create_controls(self):
        # File information
        file_frame = ttk.LabelFrame(self.controls_frame, text="File")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Load PDF button
        load_pdf_button = ttk.Button(file_frame, text="Load PDF", command=self.open_pdf)
        load_pdf_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Filename display
        ttk.Label(file_frame, text="Filename:").pack(anchor=tk.W, padx=5)
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(file_frame, textvariable=self.filename_var, state="readonly")
        filename_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Parent directory display
        ttk.Label(file_frame, text="Parent directory:").pack(anchor=tk.W, padx=5)
        self.parent_dir_var = tk.StringVar()
        parent_dir_entry = ttk.Entry(file_frame, textvariable=self.parent_dir_var, state="readonly")
        parent_dir_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Grandparent directory display
        ttk.Label(file_frame, text="Grandparent directory:").pack(anchor=tk.W, padx=5)
        self.grandparent_dir_var = tk.StringVar()
        grandparent_dir_entry = ttk.Entry(file_frame, textvariable=self.grandparent_dir_var, state="readonly")
        grandparent_dir_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Page navigation
        nav_frame = ttk.LabelFrame(self.controls_frame, text="Page Navigation")
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        page_frame = ttk.Frame(nav_frame)
        page_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_button = ttk.Button(page_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT)
        
        self.page_label = ttk.Label(page_frame, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(page_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.LEFT)
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(self.controls_frame, text="Zoom")
        zoom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        zoom_slider_frame = ttk.Frame(zoom_frame)
        zoom_slider_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(zoom_slider_frame, text="Zoom:").pack(side=tk.LEFT)
        self.zoom_slider = ttk.Scale(zoom_slider_frame, from_=10, to=300, orient=tk.HORIZONTAL, 
                                     value=100, command=self.set_zoom)
        self.zoom_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Annotation controls
        annotation_frame = ttk.LabelFrame(self.controls_frame, text="Annotation")
        annotation_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid layout for buttons
        button_frame = ttk.Frame(annotation_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1
        self.rect_button = ttk.Button(button_frame, text="Draw Rect.", command=lambda: self.set_tool("rectangle"))
        self.rect_button.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        
        self.polygon_button = ttk.Button(button_frame, text="Draw Polygon", command=lambda: self.set_tool("polygon"))
        self.polygon_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Row 2
        self.select_button = ttk.Button(button_frame, text="Select", command=lambda: self.set_tool("select"))
        self.select_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.color_button = ttk.Button(button_frame, text="Color", command=self.choose_color)
        self.color_button.grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        # Custom color buttons with labels - Row 3 and 4
        # Define colors and labels
        color_labels = [
            ("#F53C14", "Text, titles"),        # Red
            ("#F56E14", "Text, authors"),       # Orange
            ("#F5C814", "Text, abstract"),      # Yellow
            ("#97F514", "Text, body"),          # Yellow-green
            ("#B57422", "Text, author info"),   # Burnt orange
            ("#14BA94", "Text, caption"),       # Green
            ("#2CA6DE", "Text, references"),    # Blue
            ("#6725F7", "Figure"),              # Blurple
            ("#CD25F7", "Table"),               # Pink-Purple
            ("#DE2CD6", "Special-1"),           # Bright pink
            ("#F725A3", "Special-2"),           # Bright pink
            ("#F01D52", "Special-3")            # Bright pink
        ]
        
        # Create color buttons in a grid layout (4 per row)
        for i, (color, label) in enumerate(color_labels):
            row = 2 + (i // 3)  # Start at row 2 (after Draw Rect. and Color buttons)
            col = i % 3
            
            # Create a frame to hold the button and label
            item_frame = ttk.Frame(button_frame)
            item_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            
            # Create colored button with label
            color_btn = tk.Button(item_frame, bg=color, width=2, height=1,
                                 command=lambda c=color: self.set_custom_color(c))
            color_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Create label (smaller font to fit)
            label_text = tk.Label(item_frame, text=label, anchor="w", font=("Arial", 7))
            label_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Row 5 (after custom colors)
        self.modify_button = ttk.Button(button_frame, text="Modify", command=self.modify_polygon)
        self.modify_button.grid(row=6, column=0, padx=2, pady=2, sticky="ew")
        
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_selected)
        self.clear_button.grid(row=6, column=1, padx=2, pady=2, sticky="ew")
        
        # Row 6
        self.clear_all_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        self.clear_all_button.grid(row=7, column=0, columnspan=2, padx=2, pady=2, sticky="ew")
        
        # Configure grid columns to have equal width
        for i in range(4):
            button_frame.columnconfigure(i, weight=1)
    
    def set_tool(self, tool):
        self.current_tool = tool
        if tool == "select":
            self.canvas.config(cursor="arrow")
        else:
            self.canvas.config(cursor="crosshair")
            
    def set_custom_color(self, color):
        """Set the current color to the selected custom color"""
        self.current_color = color
        self.current_annotation_type = self.annotation_color_dict[color]
        
        # Add to used colors if not already there
        if self.current_color not in self.used_colors:
            self.used_colors.append(self.current_color)
    
    def choose_color(self):
        color = colorchooser.askcolor(color=self.current_color, 
                                     title="Choose a color")
        if color[1]:  # If a color was selected
            self.current_color = color[1]
            
            # Add to used colors if not already there
            if self.current_color not in self.used_colors:
                self.used_colors.append(self.current_color)
    
    def open_pdf(self):

        #Reset all polygons
        self.polygons = {}  # Dictionary to store polygons by page: {page_num: [(polygon, color), ...]}
        self.current_polygon = []
        self.selected_polygon_index = -1
        self.polygon_dict = {}  # Dictionary to store polygons and their content

        file_path = filedialog.askopenfilename(
            title="Open PDF", 
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            try:
                self.pdf_document = fitz.open(file_path)
                self.current_page = 0
                self.update_page_display()
                self.polygons = {}  # Reset polygons
                self.polygon_dict = {}  # Reset polygon dictionary
                self.page_label.config(text=f"Page: {self.current_page + 1}/{self.pdf_document.page_count}")
                
                # Update file information
                self.filepath = file_path
                filename = os.path.basename(file_path)
                parent_dir = os.path.basename(os.path.dirname(file_path))
                grandparent_dir = os.path.dirname(os.path.dirname(file_path))
                
                self.filename_var.set(filename)
                self.parent_dir_var.set(parent_dir)
                self.grandparent_dir_var.set(grandparent_dir)

                filename_guess = os.path.join(os.path.dirname(self.filepath), os.path.splitext(filename)[0] + "_annotations.json")
                try:
                    self.load_annotations(filename_guess)
                except:
                    messagebox.showerror("Note:", f"Could not find prior annotations. \n Looked for {filename_guess}")

                
            except Exception as e:
                messagebox.showerror("Error", f"Error opening PDF: {e}")
        
    def update_page_display(self):
        if self.pdf_document:
            # Render the PDF page
            page = self.pdf_document[self.current_page]
            matrix = fitz.Matrix(self.zoom_factor * 1.2, self.zoom_factor * 1.2)  # Adjust for screen DPI
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to PIL Image
            img_data = pix.samples
            img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
            
            # Convert to Tkinter PhotoImage
            self.canvas_image = ImageTk.PhotoImage(img)
            
            # Update canvas
            if self.canvas_image_id:
                self.canvas.delete(self.canvas_image_id)
            
            self.canvas_image_id = self.canvas.create_image(0, 0, image=self.canvas_image, anchor=tk.NW)
            
            # Update canvas scroll region
            self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
            
            # Draw polygons for current page
            self.redraw_polygons()
    
    def next_page(self):
        if self.pdf_document and self.current_page < self.pdf_document.page_count - 1:
            self.current_page += 1
            self.update_page_display()
            self.page_label.config(text=f"Page: {self.current_page + 1}/{self.pdf_document.page_count}")
    
    def prev_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()
            self.page_label.config(text=f"Page: {self.current_page + 1}/{self.pdf_document.page_count}")
    
    def set_zoom(self, value):
        self.zoom_factor = float(value) / 100.0
        if self.pdf_document:
            self.update_page_display()
    
    def on_canvas_click(self, event):
        if not self.pdf_document:
            return
        
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.editing_polygon:
            # Check if clicking on a control point
            for i, point in enumerate(self.editing_points):
                # Check if click is within control point square (10x10 pixels)
                if abs(x - point[0]) <= 5 and abs(y - point[1]) <= 5:
                    self.dragging_point = True
                    self.dragging_point_index = i
                    return
            
            # If not clicking on a control point, exit edit mode
            self.editing_polygon = False
            self.editing_points = None
            self.editing_index = -1
            self.select_polygon((x, y))
            self.redraw_polygons()
        elif self.current_tool == "select":
            # Try to select a polygon
            self.select_polygon((x, y))
            self.redraw_polygons()
        elif self.current_tool == "polygon":
            # Add a point to the current polygon
            # Check if we're closing the polygon (clicking near the first point)
            if len(self.current_polygon) > 2:
                first_point = self.current_polygon[0]
                # If close to the first point, close the polygon
                if ((x - first_point[0])**2 + (y - first_point[1])**2) < 100:  # Within 10 pixels
                    self.add_polygon(self.current_polygon)
                    self.current_polygon = []
                    return
            
            self.current_polygon.append((x, y))
            self.redraw_polygons()
        elif self.current_tool == "rectangle":
            # For rectangle, we need just two points (start and end)
            if len(self.current_polygon) == 0:
                # First point - start of rectangle
                self.current_polygon.append((x, y))
            elif len(self.current_polygon) == 1:
                # Second point - end of rectangle
                # Create a rectangle from the two points
                x1, y1 = self.current_polygon[0]
                x2, y2 = x, y
                
                # Convert to polygon points (4 corners)
                rect_points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                self.add_polygon(rect_points)
                self.current_polygon = []
            self.redraw_polygons()
    
    def on_canvas_drag(self, event):
        if not self.pdf_document:
            return
        
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.dragging_point and self.dragging_point_index >= 0:
            # Update the position of the dragged point
            self.editing_points[self.dragging_point_index] = (x, y)
            self.redraw_polygons()
    
    def on_canvas_release(self, event):
        if self.dragging_point:
            # Convert the edited screen points back to PDF coordinates
            pdf_points = self.screen_to_pdf_coords(self.editing_points)
            
            # Get the current page's polygons
            page_polygons = self.polygons.get(self.current_page, [])
            if page_polygons:
                color = page_polygons[self.editing_index][1]
                
                # Update the polygon in the list
                page_polygons[self.editing_index] = (pdf_points, color)
                
                # Update the polygon in the dictionary
                for key, value in self.polygon_dict.items():
                    if value["page"] == self.current_page and value["points"] == page_polygons[self.editing_index][0]:
                        value["points"] = pdf_points
                        break
            
            self.dragging_point = False
            self.dragging_point_index = -1
            self.redraw_polygons()
    
    def on_canvas_motion(self, event):
        if not self.pdf_document:
            return
        
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # If we're drawing a polygon or rectangle and have at least one point, redraw to show the preview
        if (self.current_tool == "polygon" or self.current_tool == "rectangle") and len(self.current_polygon) > 0:
            self.redraw_polygons(mouse_pos=(x, y))
    
    def on_pan_start(self, event):
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="fleur")  # Change cursor to indicate panning
    
    def on_pan_motion(self, event):
        if self.panning:
            # Calculate the movement delta
            dx = self.pan_start_x - event.x
            dy = self.pan_start_y - event.y
            
            # Scroll the canvas
            self.canvas.xview_scroll(dx, "units")
            self.canvas.yview_scroll(dy, "units")
            
            # Update the start position
            self.pan_start_x = event.x
            self.pan_start_y = event.y
    
    def on_pan_end(self, event):
        self.panning = False
        self.canvas.config(cursor="arrow" if self.current_tool == "select" else "crosshair")
    
    def on_mouse_wheel(self, event):
        # Determine the direction and amount to zoom
        if event.num == 4 or event.delta > 0:  # Scroll up or positive delta
            delta = 5  # Zoom in
        elif event.num == 5 or event.delta < 0:  # Scroll down or negative delta
            delta = -5  # Zoom out
        else:
            return
        
        # Get current zoom value
        current_zoom = self.zoom_slider.get()
        
        # Calculate new zoom value
        new_zoom = current_zoom + delta
        
        # Clamp to slider range
        new_zoom = max(10, min(new_zoom, 300))
        
        # Update zoom slider
        self.zoom_slider.set(new_zoom)
    
    def on_escape(self, event):
        # Cancel the current polygon
        self.current_polygon = []
        self.redraw_polygons()
    
    def add_polygon(self, points):
        if len(points) >= 3:
            # Convert screen coordinates to PDF coordinates for storage
            pdf_points = self.screen_to_pdf_coords(points)
            
            # Initialize the current page's polygon list if it doesn't exist
            if self.current_page not in self.polygons:
                self.polygons[self.current_page] = []
            
            # Store the polygon in PDF coordinates
            self.polygons[self.current_page].append((pdf_points, self.current_color))
            
            # Extract content using PDF coordinates
            self.extract_content_in_polygon(pdf_points, is_pdf_coords=True)
            self.redraw_polygons()
    
    def pdf_to_screen_coords(self, pdf_points):
        """Convert PDF coordinates to screen coordinates"""
        if not self.pdf_document:
            return pdf_points
            
        pdf_page = self.pdf_document[self.current_page]
        page_width = pdf_page.rect.width
        page_height = pdf_page.rect.height
        
        # Get the current image dimensions from the canvas
        img_width = self.canvas_image.width()
        img_height = self.canvas_image.height()
        
        # Calculate the scale factor
        scale_x = img_width / page_width
        scale_y = img_height / page_height
        
        # Convert points to screen coordinates
        return [(x * scale_x, y * scale_y) for x, y in pdf_points]
    
    def screen_to_pdf_coords(self, points):
        """Convert screen coordinates to PDF coordinates"""
        if not self.pdf_document:
            return points
            
        pdf_page = self.pdf_document[self.current_page]
        page_width = pdf_page.rect.width
        page_height = pdf_page.rect.height
        
        # Get the current image dimensions from the canvas
        img_width = self.canvas_image.width()
        img_height = self.canvas_image.height()
        
        # Calculate the scale factor
        scale_x = page_width / img_width
        scale_y = page_height / img_height
        
        # Convert points to PDF coordinates
        return [(x * scale_x, y * scale_y) for x, y in points]
    
    def extract_content_in_polygon(self, points, is_pdf_coords=False):
        if not self.pdf_document:
            return
        
        # If points are not already in PDF coordinates, convert them
        pdf_points = points if is_pdf_coords else self.screen_to_pdf_coords(points)
        
        # Extract text within the polygon
        pdf_page = self.pdf_document[self.current_page]
        text_instances = pdf_page.get_text("dict")["blocks"]
        polygon_content = []
        
        # Simple check if a point is inside a polygon (ray casting algorithm)
        def is_point_in_polygon(point, polygon):
            x, y = point
            n = len(polygon)
            inside = False
            
            p1x, p1y = polygon[0]
            for i in range(1, n + 1):
                p2x, p2y = polygon[i % n]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y
            
            return inside
        
        # Extract text that falls within the polygon
        for block in text_instances:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        bbox = span.get("bbox")
                        if bbox:
                            # Check if any corner of the text bbox is inside the polygon
                            corners = [
                                (bbox[0], bbox[1]),  # top-left
                                (bbox[2], bbox[1]),  # top-right
                                (bbox[2], bbox[3]),  # bottom-right
                                (bbox[0], bbox[3])   # bottom-left
                            ]
                            
                            if any(is_point_in_polygon(corner, pdf_points) for corner in corners):
                                polygon_content.append({
                                    "text": span.get("text", ""),
                                    "bbox": bbox
                                })
        
        # Store in the dictionary with a unique key
        key = f"polygon_{len(self.polygon_dict) + 1}"
        self.polygon_dict[key] = {
            "points": pdf_points,  # Store PDF coordinates
            "color": self.current_color,
            "label": self.current_annotation_type,
            "page": self.current_page,
            "content": polygon_content
        }
    
    def select_polygon(self, pos):
        if not self.pdf_document:
            return False
        
        x, y = pos
        
        # Get polygons for current page
        page_polygons = self.polygons.get(self.current_page, [])
        
        for i, (pdf_points, _) in enumerate(page_polygons):
            # Convert PDF coordinates to screen coordinates
            screen_points = self.pdf_to_screen_coords(pdf_points)
            
            # Check if the point is inside the polygon
            if self.is_point_in_polygon((x, y), screen_points):
                self.selected_polygon_index = i
                return True
        
        self.selected_polygon_index = -1
        return False
    
    def is_point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def modify_polygon(self):
        # Get polygons for current page
        page_polygons = self.polygons.get(self.current_page, [])
        
        if self.selected_polygon_index >= 0 and self.selected_polygon_index < len(page_polygons):
            # Toggle edit mode for the selected polygon
            if self.editing_polygon:
                self.editing_polygon = False
                self.editing_points = None
                self.editing_index = -1
                self.dragging_point = False
            else:
                self.editing_polygon = True
                self.editing_index = self.selected_polygon_index
                # Convert PDF coordinates to screen coordinates for editing
                pdf_points = page_polygons[self.selected_polygon_index][0]
                self.editing_points = self.pdf_to_screen_coords(pdf_points)
                self.dragging_point = False
                self.dragging_point_index = -1
            
            # Redraw to show edit handles
            self.redraw_polygons()
    
    def clear_selected(self):
        # Get polygons for current page
        page_polygons = self.polygons.get(self.current_page, [])
        
        if self.selected_polygon_index >= 0 and self.selected_polygon_index < len(page_polygons):
            # Remove from dictionary
            pdf_points = page_polygons[self.selected_polygon_index][0]
            for key, value in list(self.polygon_dict.items()):
                if value["page"] == self.current_page and np.array_equal(value["points"], pdf_points):
                    del self.polygon_dict[key]
                    break
            
            # Remove from polygons list
            del page_polygons[self.selected_polygon_index]
            self.polygons[self.current_page] = page_polygons
            self.selected_polygon_index = -1
            self.redraw_polygons()
    
    def clear_all(self):
        # Clear all polygons on the current page
        if self.current_page in self.polygons:
            self.polygons[self.current_page] = []
        
        # Remove all entries for the current page from the dictionary
        self.polygon_dict = {k: v for k, v in self.polygon_dict.items() if v["page"] != self.current_page}
        
        self.selected_polygon_index = -1
        self.redraw_polygons()
    
    def save_annotations(self):
        if not self.polygon_dict:
            messagebox.showinfo("Info", "No annotations to save.")
            return

        filename_guess = os.path.join(os.path.dirname(self.filepath), os.path.splitext(self.filepath)[0] + "_annotations.json")
            
        file_path = filedialog.asksaveasfilename(
            title="Save Annotations",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile= filename_guess
            )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.polygon_dict, f)
                messagebox.showinfo("Success", "Annotations saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving annotations: {e}")
    
    def load_annotations(self, file_path=None):
        if file_path == None:
            file_path = filedialog.askopenfilename(
                title="Load Annotations",
                filetypes=[("JSON Files", "*.json")]
                )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.polygon_dict = json.load(f)
                
                # Rebuild polygons for all pages
                self.polygons = {}
                for key, value in self.polygon_dict.items():
                    page = value["page"]
                    pdf_points = value["points"]
                    color = value["color"]
                    
                    if page not in self.polygons:
                        self.polygons[page] = []
                    
                    self.polygons[page].append((pdf_points, color))
                
                self.redraw_polygons()
                messagebox.showinfo("Success", "Annotations loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading annotations: {e}")
    
    def show_annotation_dict(self):
        """Display the annotation dictionary in a new window"""
        if not self.polygon_dict:
            messagebox.showinfo("Info", "No annotations to display.")
            return
        
        # Create a new window
        annotation_window = tk.Toplevel(self.root)
        annotation_window.title("Annotation Dictionary")
        annotation_window.geometry("600x400")
        
        # Create a scrolled text widget
        text_area = scrolledtext.ScrolledText(annotation_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format and display the annotation dictionary
        formatted_text = json.dumps(self.polygon_dict, indent=4)
        text_area.insert(tk.END, formatted_text)
        text_area.config(state=tk.DISABLED)  # Make it read-only
    
    def analyze_content(self):
        """Placeholder for content analysis feature"""
        messagebox.showinfo("Info", "Content analysis feature not implemented yet.")
    
    def redraw_polygons(self, mouse_pos=None):
        """Redraw all polygons and the current polygon being created"""
        if not self.pdf_document:
            return
        
        # Clear all existing polygon drawings
        self.canvas.delete("polygon")
        
        # Draw all saved polygons for the current page
        page_polygons = self.polygons.get(self.current_page, [])
        
        for i, (pdf_points, color) in enumerate(page_polygons):
            # Convert PDF coordinates to screen coordinates
            screen_points = self.pdf_to_screen_coords(pdf_points)
            
            # Flatten the list of points for the canvas create_polygon function
            flat_points = [coord for point in screen_points for coord in point]
            
            # Draw the polygon
            if i == self.selected_polygon_index:
                # Highlight the selected polygon with yellow outline
                self.canvas.create_polygon(flat_points, 
                                          outline="yellow", 
                                          fill=color, 
                                          stipple="gray50",  # 50% transparency
                                          width=3,
                                          tags="polygon")
                
                # Draw control points if in edit mode
                if self.editing_polygon and i == self.editing_index:
                    for point in self.editing_points:
                        # Draw a square handle at each point
                        x, y = point
                        self.canvas.create_rectangle(x-5, y-5, x+5, y+5,
                                                   outline="black",
                                                   fill="yellow",
                                                   tags="polygon")
            else:
                self.canvas.create_polygon(flat_points, 
                                          outline=color, 
                                          fill=color, 
                                          stipple="gray50",  # 50% transparency
                                          width=2,
                                          tags="polygon")
        
        # Draw the polygon being created
        if self.current_tool == "polygon" and len(self.current_polygon) > 0:
            # Draw lines between points
            for i in range(len(self.current_polygon) - 1):
                x1, y1 = self.current_polygon[i]
                x2, y2 = self.current_polygon[i+1]
                self.canvas.create_line(x1, y1, x2, y2, 
                                       fill=self.current_color, 
                                       width=2,
                                       tags="polygon")
            
            # Draw from last point to current mouse position if there's at least one point
            if len(self.current_polygon) > 0 and mouse_pos:
                x1, y1 = self.current_polygon[-1]
                x2, y2 = mouse_pos
                self.canvas.create_line(x1, y1, x2, y2, 
                                       fill=self.current_color, 
                                       width=2,
                                       tags="polygon")
            
            # Draw points
            for x, y in self.current_polygon:
                self.canvas.create_oval(x-3, y-3, x+3, y+3, 
                                      fill=self.current_color,
                                      outline=self.current_color,
                                      tags="polygon")
        
        # Draw the rectangle being created
        elif self.current_tool == "rectangle" and len(self.current_polygon) == 1 and mouse_pos:
            x1, y1 = self.current_polygon[0]
            x2, y2 = mouse_pos
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                       outline=self.current_color,
                                       fill=self.current_color,
                                       stipple="gray50",  # 50% transparency
                                       width=2,
                                       tags="polygon")
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFAnnotator(root)
    root.mainloop()
