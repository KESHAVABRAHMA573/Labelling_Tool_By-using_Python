import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk, ImageDraw
import json
from tkinter import ttk
import struct
import numpy as np
import cv2
import csv
import math

class Load_file:
    def __init__(self):
        self.root = tk.Tk()
        topbar = tk.Frame(self.root, bg="white")
        topbar.pack(side="top", fill="x")
        
        
        file_btn = tk.Menubutton(topbar, text="File", font=("Helvetica", 10, "bold"), bg="white")
        file_menu = tk.Menu(file_btn, tearoff=0)
        file_menu.add_command(label="Select File", command=self.select_file)
        file_menu.add_command(label="Select Folder", command=self.select_folder)
        file_menu.add_command(label="Select .txt file", command=self.select_txt_file)
        file_btn.config(menu=file_menu)
        file_btn.pack(side="left", padx=10, pady=(6,5))

        convert_btn = tk.Menubutton(topbar, text="Convert", font=("Helvetica", 10, "bold"), bg="white")
        convert_menu = tk.Menu(convert_btn, tearoff=0)
        convert_menu.add_command(label="Json to Dat", command=self.convert_json_to_dat)
        convert_menu.add_command(label="Json to Txt", command=self.convert_json_to_txt)
        convert_menu.add_command(label="Json to cargoMarkerxml", command=self.convert_json_to_cargomarkerxml)
        convert_btn.config(menu=convert_menu)
        convert_btn.pack(side="left", padx=10, pady=(6,5))

        self.coord_label = tk.Label(topbar, text="X: 0, Y: 0", font=("Helvetica", 10,"bold"), bg="white")
        self.coord_label.pack(side="right", padx=10, pady=5)

        self.root.title("Labelling_TooL")
        self.root.state('zoomed')


        self.ImagePath = []
        self.CurrentIndex = 0
        self.labelling = 0
        self.points = []
        self.polygon_id = []
        self.temp_shapes = []     
        self.new_shapes = []
        self.shapes_modified = False
        self.temp_line_ids = []
        self.temp_point_ids = []
        self.edit_undo_stack = []
        self.edit_redo_stack = []
        self.dat_shapes = []
        self.dropdown_vars = []
        self.dropdown_items = []
        self.orig_img = None      
        self.last_saved_png_flag = False
        self.img = None           
        self.img_tk = None
        self.mask_data = None
        self.mask_visible = False
        self.mask_overlay_id = None
        self.tk_mask_overlay = None
        self.img_x = 0
        self.img_y = 0
        self.mode = "label"
        self.raw_np = None
        self.editing_shape_index = None
        self.editing_segment_index = None
        self.intensive_zoom_mode = False
        self.zoom_rect_id = None
        self.zoom_start = None
        self.image_saved_once = False
        self.last_saved_format = None
        self.initial_display_img = None
        self.dragging_segment = None
        self.drag_preview_id = None
        self.label_popup_open = False
        self.label_popup_ref = None

        self.zoom_scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.min_zoom = 0.1
        self.max_zoom = 8.0

        self.top_frame = tk.Frame(self.root, bg="white")
        self.top_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.root, bg="lightgray")
        self.bottom_frame.pack(side="bottom", fill="x")

        self.canvas_frame = tk.Frame(self.top_frame)
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.gamma_var = tk.DoubleVar(value=1.0)


        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
    
        self.enable_click_to_zoom()

        self.Load1_var = tk.StringVar()
        self.Load1 = tk.Button(self.bottom_frame, textvariable=self.Load1_var, width=45, anchor="w", command=self.open_dropdown)
        self.Load1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.dropdown_items = []  # (index, path, is_labeled)
        self.dropdown_popup = None

        self.rect = tk.Button(self.bottom_frame ,text="Rectangle Zoom",width=14, command=self.enable_drag_zoom)
        self.rect.grid(row=2,rowspan=2,column=6,padx=10,pady=10)
        
        next_prev_frame = tk.Frame(self.bottom_frame, bg="lightgray")
        next_prev_frame.grid(row=0, column=2, padx=10, pady=10)

        self.prev = tk.Button(next_prev_frame, text="Prev", width=6, command=self.previousPressed)
        self.prev.pack(side="left", padx=(0, 5))

        self.next = tk.Button(next_prev_frame, text="Next", width=6, command=self.nextPressed)
        self.next.pack(side="left")
        
        edit_delete_frame = tk.Frame(self.bottom_frame, bg="lightgray")
        edit_delete_frame.grid(row=1, column=5, padx=10, pady=10)
        
        self.Edit = tk.Button(edit_delete_frame, text="Edit", width=6,command=self.editPressed)
        self.Edit.pack(side="left", padx=(0, 5))
        
        self.Delete = tk.Button(edit_delete_frame, text="Delete", width=6,command=self.deletePressed)
        self.Delete.pack(side="left")
        
        self.save = tk.Button(self.bottom_frame ,text="Save",width=14,command=self.savePressed)
        self.save.grid(row=2, column=5,rowspan=2, padx=10, pady=10)
        
        self.reset_btn = tk.Button(self.bottom_frame, text="Reset",width=14, command=self.reset_brightness_contrast)
        self.reset_btn.grid(row=2, column=7, padx=0, pady=0)

        brightness_frame = tk.Frame(self.bottom_frame)
        brightness_frame.grid(row=0, column=8, columnspan=4, sticky="w", padx=10, pady=2)

        tk.Label(brightness_frame, text="Brightness", width=10, anchor="w").pack(side="left")
        tk.Button(brightness_frame, text="◀", width=2, command=lambda: self.adjust_brightness(-0.1)).pack(side="left")
        tk.Scale(brightness_frame, from_=0.0, to=2.0, resolution=0.1, orient="horizontal",
         variable=self.brightness_var, command=self.update_image, length=200).pack(side="left")
        tk.Button(brightness_frame, text="▶", width=2, command=lambda: self.adjust_brightness(0.1)).pack(side="left")

        contrast_frame = tk.Frame(self.bottom_frame)
        contrast_frame.grid(row=1, column=8, columnspan=4, sticky="w", padx=10, pady=2)

        tk.Label(contrast_frame, text="Contrast", width=10, anchor="w").pack(side="left")
        tk.Button(contrast_frame, text="◀", width=2, command=lambda: self.adjust_contrast(-0.1)).pack(side="left")
        tk.Scale(contrast_frame, from_=0.1, to=2.0, resolution=0.1, orient="horizontal",
         variable=self.contrast_var, command=self.update_image, length=200).pack(side="left")
        tk.Button(contrast_frame, text="▶", width=2, command=lambda: self.adjust_contrast(0.1)).pack(side="left")
        
        gamma_frame = tk.Frame(self.bottom_frame)
        gamma_frame.grid(row=2, column=8, columnspan=4, sticky="w", padx=10, pady=2)

        tk.Label(gamma_frame, text="Gamma", width=10, anchor="w").pack(side="left")
        tk.Button(gamma_frame, text="◀", width=2, command=lambda: self.adjust_gamma(-0.1)).pack(side="left")
        tk.Scale(gamma_frame, from_=0.1, to=2.0, resolution=0.1, orient="horizontal",
         variable=self.gamma_var, command=self.update_image, length=200).pack(side="left")
        tk.Button(gamma_frame, text="▶", width=2, command=lambda: self.adjust_gamma(0.1)).pack(side="left")

        self.Labeling = tk.Button(self.bottom_frame, text="Start labelling",width=14, command=self.labellingPressed)
        self.Labeling.grid(row=0, column=4, padx=10, pady=10)

        undo_redo_frame = tk.Frame(self.bottom_frame, bg="lightgray")
        undo_redo_frame.grid(row=0, column=5, padx=10, pady=10)

        self.Undo = tk.Button(undo_redo_frame, text="Undo", width=6, command=self.undoPressed)
        self.Undo.pack(side="left", padx=(0, 5))

        self.Redo = tk.Button(undo_redo_frame, text="Redo", width=6, command=self.redoPressed)
        self.Redo.pack(side="left")

        self.fitWindow=tk.Button(self.bottom_frame,text="Fit Window",width=14,command=self.fitWindowPressed)
        self.fitWindow.grid(row=0,column=7 ,padx=10,pady=10)


        self.formatSelector = tk.StringVar(value="json")
        
        format_frame = tk.Frame(self.bottom_frame, bg="lightgray")
        format_frame.grid(row=1, column=4, padx=10, pady=0,sticky="n")

        self.json = tk.Radiobutton(format_frame, text="Json",variable=self.formatSelector, value="json")
        self.json.pack(anchor="w",pady=(8, 0))

        self.both = tk.Radiobutton(format_frame, text="Json & dat",variable=self.formatSelector, value="both")
        self.both.pack(anchor="w")

        self.ShowMaskFile = tk.Button(self.bottom_frame, text="Show_DAT_File",width=15)
        self.ShowMaskFile.grid(row=2, column=2,rowspan=2, padx=10, pady=10)
        self.ShowMaskFile.bind("<ButtonPress-1>", self.show_dat_file)
        self.ShowMaskFile.bind("<ButtonRelease-1>", self.close_msk_file)
        
        self.show_mask_var = tk.IntVar(value=False)
        self.mask_checkbox = tk.Checkbutton(self.bottom_frame, text="Save dat as PNG", variable=self.show_mask_var)
        self.mask_checkbox.grid(row=1, column=2, padx=10, pady=10,sticky="w")

        self.zoomin = tk.Button(self.bottom_frame, text="Zoom_in",width=14, command=self.zoomInPressed)
        self.zoomin.grid(row=1, column=6,padx=10,pady=10)

        self.zoomout = tk.Button(self.bottom_frame, text="Zoom_out", width=14,command=self.zoomOutPressed)
        self.zoomout.grid(row=1, column=7,padx=10,pady=10)
        
        self.toggle_mode_btn = tk.Button(self.bottom_frame, text="🖐️Palm Mode",width=14, command=self.toggle_mode)
        self.toggle_mode_btn.grid(row=0, column=6, padx=10, pady=5)
    
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        self.root.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 * int(e.delta / 120), "units"))
        self.root.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units")) 
        self.root.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))   
        self.root.bind("<Delete>", lambda event: self.undoPressed())
        self.root.bind("<l>", lambda event: self.toggle_mode())
        self.root.bind("<Control-s>", lambda event: self.handle_s_key())
        self.root.bind(".", lambda event: self.nextPressed())       
        self.root.bind(",", lambda event: self.previousPressed())   
        self.root.bind("<Control-z>", lambda event: self.undoPressed())
        self.root.bind("<Control-y>", lambda event: self.redoPressed())
        self.root.bind("<Control-=>", lambda event: self.zoomInPressed())
        self.root.bind("<Control-minus>", lambda event: self.zoomOutPressed())
        self.root.bind("<s>",lambda event : self.labellingPressed())
        self.root.bind("<f>",lambda event : self.fitWindowPressed())
        self.root.bind("<r>",lambda event : self.reset_brightness_contrast())
        self.root.bind("<Alt-f>",lambda event : self.select_file())
        self.root.bind("<Alt-o>",lambda event : self.select_folder())
        self.root.bind("<Alt-l>",lambda event : self.select_txt_file())
        self.root.bind("<Alt-c>",lambda event : self.show_convert_options())
        
        self.root.bind("<z>", lambda e: self.enable_drag_zoom())
        self.root.mainloop()
#----------------------------------------------------
    def select_file(self):
        file_paths = filedialog.askopenfilenames(
        title="Select image files",
        filetypes=[
            ("All files", "*.*"),
            ("JPG files", "*.jpg"),
            ("JPEG files", "*.jpeg"),
            ("PNG files", "*.png"),
            ("CargoImage files", "*.cargoimage"),
            ("IMG files", "*.img"),            
        ]
    )
        if not file_paths:
            return

        self.ImagePath.clear()

        if len(file_paths) == 1 and file_paths[0].lower().endswith(".txt"):
       
            self.Load1_var.set(file_paths[0])
            try:
                with open(file_paths[0], "r") as f:
                    lines = f.read().splitlines()
                    for line in lines:
                        stripped = line.strip().strip('"')
                        if stripped.lower().endswith(('.jpg', '.jpeg', '.png', '.cargoimage', '.img')) and os.path.exists(stripped):
                            self.ImagePath.append(stripped)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
                return
        else:
        
            self.ImagePath.extend(file_paths)
            self.Load1_var.set(f"{len(file_paths)} images selected")

        if not self.ImagePath:
            messagebox.showerror("Empty Selection", "No valid image paths found")
            return

        self.populate_dropdown()
        self.root.focus_set()
        
        
    def select_txt_file(self):
        file_paths = filedialog.askopenfilenames(
        title="Select image files",
        filetypes=[("Text files", "*.txt")])
        if not file_paths:
            return

        self.ImagePath.clear()

        if len(file_paths) == 1 and file_paths[0].lower().endswith(".txt"):
            self.Load1_var.set(file_paths[0])
            try:
                with open(file_paths[0], "r") as f:
                    lines = f.read().splitlines()
                    for line in lines:
                        stripped = line.strip().strip('"')
                        if stripped.lower().endswith(('.jpg', '.jpeg', '.png', '.cargoimage', '.img')) and os.path.exists(stripped):
                            self.ImagePath.append(stripped)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
                return
        else:       
            self.ImagePath.extend(file_paths)
            self.Load1_var.set(f"{len(file_paths)} images selected")
        if not self.ImagePath:
            messagebox.showerror("Empty Selection", "No valid image paths found")
            return
        self.populate_dropdown()
        self.root.focus_set()
        
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Select a folder containing images")
        if not folder_path:
            return
        self.Load1_var.set(folder_path)
        try:
            allowed_exts = self.load_allowed_extensions()
            self.ImagePath.clear()
            for root, _, files in os.walk(folder_path):
                for fname in files:
                    if any(fname.lower().endswith(ext) for ext in allowed_exts):
                        full_path = os.path.join(root, fname)
                        self.ImagePath.append(full_path)
            if not self.ImagePath:
                messagebox.showerror("Empty Folder", "No valid image files found in folder")
                return
            self.populate_dropdown()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load folder:\n{e}")
        self.root.focus_set()
    
    def load_allowed_extensions(self, config_path=r"C:\Users\kgopidesi\Downloads\Labelling_Tool_Config.txt"):
        try:
            with open(config_path, "r") as f:
                line = f.readline()
                parts = [part.strip().lower() for part in line.split(",")]
                return [ext for ext in parts[1:] if ext]  # skip header
        except Exception as e:
            print("Failed to load filter config:", e)
            return ['.jpg', '.jpeg', '.png', '.cargoimage', '.img']  


    def open_dropdown(self):
        if self.dropdown_popup and self.dropdown_popup.winfo_exists():
            self.dropdown_popup.destroy()

        self.dropdown_popup = tk.Toplevel(self.root)
        self.dropdown_popup.wm_overrideredirect(True)
        self.dropdown_popup.attributes("-topmost", True)

        x = self.Load1.winfo_rootx()
        y = self.Load1.winfo_rooty() + self.Load1.winfo_height()
        self.dropdown_popup.geometry(f"+{x}+{y}")

        outer_frame = tk.Frame(self.dropdown_popup, borderwidth=1, relief="solid")
        outer_frame.pack(fill="both", expand=True)

        canvas_height = 120
        canvas_width = self.Load1.winfo_width()

        canvas = tk.Canvas(outer_frame, width=canvas_width, height=canvas_height)
        canvas.grid(row=0, column=0, sticky="nsew")

        v_scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        h_scrollbar = tk.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        canvas.grid_propagate(False)

        outer_frame.grid_rowconfigure(0, weight=1)
        outer_frame.grid_columnconfigure(0, weight=1)

        scroll_frame = tk.Frame(canvas)
        scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(scroll_window, width=scroll_frame.winfo_reqwidth())

        scroll_frame.bind("<Configure>", update_scroll_region)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self.dropdown_vars.clear()
        for i, path, is_labeled in self.dropdown_items:
            item_frame = tk.Frame(scroll_frame)
            item_frame.pack(fill="x", anchor="w")

            var = tk.IntVar(value=1 if is_labeled else 0)
            self.dropdown_vars.append(var)

            cb = tk.Checkbutton(item_frame, variable=var, state="disabled")
            cb.pack(side="left")

            label_text = f"{i+1}/{len(self.ImagePath)} — {os.path.basename(path)}"
            lbl = tk.Label(item_frame, text=label_text, anchor="w")
            lbl.pack(side="left", padx=2)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_image_from_dropdown(idx))

        def cleanup_scroll_bindings(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        self.dropdown_popup.bind("<FocusOut>", lambda e: self.dropdown_popup.destroy())
        self.dropdown_popup.bind("<Destroy>", cleanup_scroll_bindings)
        self.dropdown_popup.focus_set()

    def populate_dropdown(self):
        self.dropdown_items = []
        for i, path in enumerate(self.ImagePath):
            base = os.path.splitext(path)[0]
            json_path = base + "_label.json"
            dat_path = base + "_label.dat"
            is_labeled = os.path.exists(json_path) or os.path.exists(dat_path)
            label = f"{self.CurrentIndex + 1}/{len(self.ImagePath)} — {os.path.basename(self.ImagePath[self.CurrentIndex])}"
            self.Load1_var.set(label)

            self.dropdown_items.append((i, path, is_labeled))

        dropdown_labels = [f"{i+1}/{len(self.ImagePath)} — {os.path.basename(p)}" for i, p, _ in self.dropdown_items]
    
        last_labeled_index = -1
        for i, (_, path, labeled) in enumerate(self.dropdown_items):
            if labeled:
                last_labeled_index = i
        self.CurrentIndex = min(last_labeled_index + 1, len(self.ImagePath) - 1)

        self.showImagePaths()
        
    def edit_label_popup(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        for idx, shape in enumerate(self.temp_shapes):
            screen_pts = [
                (int(round(x * self.zoom_scale)) + self.img_x,
                int(round(y * self.zoom_scale)) + self.img_y)
                for (x, y) in shape
                ]
            flat = [coord for pt in screen_pts for coord in pt]
            if self.canvas.find_overlapping(cx, cy, cx, cy):
                polygon_id = self.polygon_id[idx]
                if polygon_id in self.canvas.find_overlapping(cx, cy, cx, cy):
                    labels = self.load_labels_from_csv()
                    if not labels:
                        messagebox.showerror("Label Error", "No labels found in CSV.")
                        return

                    popup = tk.Toplevel(self.root)
                    popup.title("Edit Label")
                    popup.geometry("250x150")
                    popup.transient(self.root)
                    popup.grab_set()

                    screen_w = popup.winfo_screenwidth()
                    screen_h = popup.winfo_screenheight()
                    popup.geometry(f"+{screen_w//2 - 125}+{screen_h//2 - 75}")

                    tk.Label(popup, text="Choose new label:").pack(pady=5)

                    current_label = self.new_shapes[idx]["label"]
                    selected_label = tk.StringVar(value=current_label)
                    dropdown = ttk.Combobox(popup, textvariable=selected_label, values=labels, state="readonly")
                    dropdown.pack(pady=5)

                    def save_label():
                        self.new_shapes[idx]["label"] = selected_label.get()
                        self.shapes_modified = True
                        popup.destroy()
                        self.show_temp_message(f"Label updated to '{selected_label.get()}'")

                    tk.Button(popup, text="Save", command=save_label).pack(pady=10)
                    return
        
    def is_image_labeled(self, path):
        base = os.path.splitext(path)[0]
        return os.path.exists(base + "_label.json") or os.path.exists(base + "_label.dat")

    def select_image_from_dropdown(self, index):
        self.CurrentIndex = index
        self.dropdown_popup.destroy()
        self.showImagePaths()

    def on_dropdown_select(self, event=None):
        selected = self.Load1.current()
        if 0 <= selected < len(self.ImagePath):
            self.CurrentIndex = selected
            self.showImagePaths()

    def editPressed(self):
        self.mode = "edit"
        self.canvas.config(cursor="arrow")
        self.labellingPressed()
        self.canvas.bind("<ButtonPress-1>", self.edit_combined_handler)
        self.canvas.bind("<B1-Motion>", self.drag_segment_preview)
        self.canvas.bind("<ButtonRelease-1>", self.finish_drag_segment)
        self.canvas.bind("<Button-3>", self.edit_label_popup)
        self.root.focus_set()
      
    def edit_combined_handler(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        for shape_index, shape in enumerate(self.temp_shapes):
            for i, (x, y) in enumerate(shape):
                px = x * self.zoom_scale + self.img_x
                py = y * self.zoom_scale + self.img_y
                dist = ((px - cx)**2 + (py - cy)**2)**0.5
                if dist < 5:
                    if len(shape) <= 3:
                        messagebox.showwarning("Edit", "Polygon must have at least 3 points.")
                        return
                    removed = shape.pop(i)
                    self.edit_undo_stack.append({
                        "shape_index": shape_index,
                        "point_index": i,
                        "removed": removed,
                        "inserted": None
                    })
                    self.edit_redo_stack.clear()
                    self.shapes_modified = True
                    self.redraw_canvas()
                    return

        self.start_drag_segment(event)

    def start_drag_segment(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        for shape_index, shape in enumerate(self.temp_shapes):
            for i in range(len(shape)):
                p1 = shape[i]
                p2 = shape[(i + 1) % len(shape)]
                x1 = p1[0] * self.zoom_scale + self.img_x
                y1 = p1[1] * self.zoom_scale + self.img_y
                x2 = p2[0] * self.zoom_scale + self.img_x
                y2 = p2[1] * self.zoom_scale + self.img_y
                dist = self.point_to_segment_distance(cx, cy, x1, y1, x2, y2)
                if dist < 5:
                    self.dragging_segment = (shape_index, i)
                    return

    def drag_segment_preview(self, event):
        if self.dragging_segment:
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            if self.drag_preview_id:
                self.canvas.delete(self.drag_preview_id)
            self.drag_preview_id = self.canvas.create_oval(
                cx - 3, cy - 3, cx + 3, cy + 3, fill="red", outline="red", tags="preview"
            )

    def finish_drag_segment(self, event):
        if self.dragging_segment:
            shape_index, segment_index = self.dragging_segment
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            img_x = (cx - self.img_x) / self.zoom_scale
            img_y = (cy - self.img_y) / self.zoom_scale
            shape = self.temp_shapes[shape_index]
            shape.insert(segment_index + 1, (img_x, img_y))
            self.edit_undo_stack.append({
            "shape_index": shape_index,
            "segment_index": segment_index,
            "inserted": (img_x, img_y),
            "removed": None
            })
            self.edit_redo_stack.clear()

            self.shapes_modified = True
            self.dragging_segment = None
            if self.drag_preview_id:
                self.canvas.delete(self.drag_preview_id)
                self.drag_preview_id = None
            self.redraw_canvas()

    def edit_click_handler(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        for shape_index, shape in enumerate(self.temp_shapes):
            for i, (x, y) in enumerate(shape):
                px = x * self.zoom_scale + self.img_x
                py = y * self.zoom_scale + self.img_y
                dist = ((px - cx)**2 + (py - cy)**2)**0.5
                if dist < 5:
                    if len(shape) <= 3:
                        messagebox.showwarning("Edit", "Polygon must have at least 3 points.")
                        self.canvas.unbind("<Button-1>")
                        self.mode = "label"
                        self.labellingPressed()
                        return
                    removed = shape.pop(i)
                    self.edit_undo_stack.append({
                        "shape_index": shape_index,
                        "point_index": i,
                        "removed": removed,
                        "inserted": None
                    })
                    self.shapes_modified = True
                    self.redraw_canvas()
                    self.labellingPressed()
                    return

        for shape_index, shape in enumerate(self.temp_shapes):
            for i in range(len(shape)):
                p1 = shape[i]
                p2 = shape[(i + 1) % len(shape)]
                x1 = p1[0] * self.zoom_scale + self.img_x
                y1 = p1[1] * self.zoom_scale + self.img_y
                x2 = p2[0] * self.zoom_scale + self.img_x
                y2 = p2[1] * self.zoom_scale + self.img_y

                dist = self.point_to_segment_distance(cx, cy, x1, y1, x2, y2)
                if dist < 5:
                    self.edit_undo_stack.append({
                        "shape_index": shape_index,
                        "segment_index": i,
                        "removed": None,
                        "inserted": None
                    })
                    
                    self.editing_shape_index = shape_index
                    self.editing_segment_index = i
                    self.canvas.bind("<Button-1>", self.insert_edit_point)
                    return

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        line_mag = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        if line_mag < 1e-6:
            return ((px - x1)**2 + (py - y1)**2)**0.5
        u = ((px - x1)*(x2 - x1) + (py - y1)*(y2 - y1)) / (line_mag**2)
        u = max(0, min(1, u))
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        return ((px - ix)**2 + (py - iy)**2)**0.5

    def edit_segment(self, shape_index, segment_index):
        shape = self.temp_shapes[shape_index]
        p1 = shape[segment_index]
        p2 = shape[(segment_index + 1) % len(shape)]

        shape.pop((segment_index + 1) % len(shape))

    def toggle_mode(self):
        if self.mode == "label":
            self.mode = "pan"
            self.canvas.config(cursor="hand2")
            self.toggle_mode_btn.config(text="➡️ Label Mode")

            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<Button-3>")
            self.root.unbind("<Delete>")

            self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<Button-3>", self.switch_to_label_mode)
        else:
            self.mode = "label"
            self.canvas.config(cursor="arrow")
            self.toggle_mode_btn.config(text="🖐️ Pan Mode")
            self.labellingPressed()
        self.root.focus_set()
        
    def switch_to_label_mode(self, event=None):
        self.mode = "label"
        self.canvas.config(cursor="arrow")
        self.toggle_mode_btn.config(text="🖐️ Pan Mode")
        self.canvas.unbind("<Button-3>")  
        self.labellingPressed()
     
    def adjust_brightness(self, delta):
        new_val = round(self.brightness_var.get() + delta, 1)
        self.brightness_var.set(new_val)
        self.update_image()

    def adjust_contrast(self, delta):
        new_val = round(self.contrast_var.get() + delta, 1)
        self.contrast_var.set(new_val)
        self.update_image()
        
    def adjust_gamma(self, delta):
        new_val = round(self.gamma_var.get() + delta, 1)
        self.gamma_var.set(max(0.1, min(3.0, new_val)))
        self.update_image()
        
    def load_labels_from_csv(self, csv_path=r"C:\Users\kgopidesi\Downloads\labels.csv"):
        labels=[]
        try :
            with open(csv_path,newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    label=row.get("label")
                    if label:
                        labels.append(label.strip())
        except Exception as e :
            messagebox.showerror("Csv Error",f"failed to load labels:\n{e}")
        return labels
    
            
    def on_mouse_down(self, event):
        if self.mode == "pan":
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            return
        if self.mode == "label":
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            img_x = (canvas_x - self.img_x) / self.zoom_scale
            img_y = (canvas_y - self.img_y) / self.zoom_scale
            
            orig_w, orig_h = self.orig_img.size
            img_x = min(max(img_x, 0), orig_w - 1)
            img_y = min(max(img_y, 0), orig_h - 1)

            self.points.append((img_x, img_y))
            self.redraw_canvas()

    def on_mouse_drag(self, event):
        if self.mode == "pan" and self.zoom_scale > self.fit_zoom_scale:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            self.img_x += dx
            self.img_y += dy
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.redraw_canvas()

    def OpenCargoImage(self, name):
        with open(name, 'rb') as f:
            f.read(8)   
            f.read(4)   
            ign = struct.unpack('<B', f.read(1))[0]
            f.read(3)   
            bpp = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<II', f.read(8))
            height, width = size[0], size[1]
            size2 = struct.unpack('<II', f.read(8))
            format1, flag = size2[0], size2[1]
            if ign == 24:
            
                _ = struct.unpack('<I', f.read(4))[0]
            f.read(8)  

            if format1 > 2:
                
                count = width * height * 2  
                data = np.frombuffer(f.read(count * 2), dtype='<u2', count=count)
                
                high = data[1::2].reshape((width, height)).T
                low  = data[0::2].reshape((width, height)).T
            else:
                count = width * height
                data = np.frombuffer(f.read(count * 2), dtype='<u2', count=count)
                high = data.reshape((width, height)).T
                low = 0

        return high, low

    def OpenIMGimage(self,name):
        with open(name, 'rb') as f:
            header = f.read(2)
            h1 = struct.unpack('<h',header)
            skip = f.read(2)
            s1 = struct.unpack('<h',skip)
            s2 = s1[0]
            skip1 = f.read(2)
            h3 = struct.unpack('<h',skip1)
            height3 = h3[0]
            skip1 = f.read(2)
            w1 = struct.unpack('<h',skip1)
            width = w1[0]
            skip1 = f.read(2)
            xPos = struct.unpack('<h',skip1)
            flag = xPos[0]
            skip1 = f.read(2)
            yPos = struct.unpack('<h',skip1)
            skip1 = f.read(2)
            flag2 = struct.unpack('<h',skip1)

            for i in range(25):
                skip1 = f.read(2)

            for i in range(s2):
                skip2 = f.read(1)
            
            height = int(height3/3)

            bytes = f.read(width * height3 * 2)
            data = np.frombuffer(bytes, dtype=np.uint16).copy()

            data = data.reshape([width,height3])

            high = np.zeros([height,width])
            low = np.zeros([height,width])
            Zimage = np.zeros([height,width])

            high= data[:,:height].T
            low= data[:,height : 2* height].T
            Zimage = data[:, 2*height : 3 * height].T

            high = np.flipud(high)
            low = np.flipud(low)
            Zimage = np.flipud(Zimage)
            
        return high, low
    
    def load_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        self.raw_np=None
        if ext == '.cargoimage':
            high, _ = self.OpenCargoImage(path)
            self.raw_np = high.copy() 
            p1, p99 = np.percentile(high, (1, 99))
            if p99 - p1 < 10:
                p1, p99 = float(high.min()), float(high.max())
            img8 = np.clip((high - p1) * 255.0 / max((p99 - p1), 1), 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img8, mode='L').convert('RGB')
        elif ext == '.img':
            high, _ = self.OpenIMGimage(path)
            self.raw_np = high.copy() 
            p1, p99 = np.percentile(high, (1, 99))
            if p99 == p1:
                p1, p99 = float(high.min()), float(high.max())
            img8 = np.clip((high - p1) * 255.0 / max((p99 - p1), 1), 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img8, mode='L').convert('RGB')
        else:
            img_cv = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img_cv is None:
                raise ValueError("Failed to load image.")
            self.raw_np = img_cv.copy() 
            if img_cv.ndim == 2:
                # grayscale (8/16-bit)
                if img_cv.dtype == np.uint16:
                    p1, p99 = np.percentile(img_cv, (1, 99))
                    if p99 == p1:
                        p1, p99 = float(img_cv.min()), float(img_cv.max())
                    img8 = np.clip((img_cv - p1) * 255.0 / max((p99 - p1), 1), 0, 255).astype(np.uint8)
                else:
                    img8 = img_cv.astype(np.uint8)
                pil_img = Image.fromarray(img8, mode='L').convert('RGB')
            else:
                if img_cv.dtype == np.uint16:
                    img_cv = cv2.convertScaleAbs(img_cv, alpha=(255.0 / 65535.0))
                pil_img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        return pil_img
    
    def showImagePaths(self):
        path = self.ImagePath[self.CurrentIndex]
        if hasattr(self, "Load1_var"):
            label = f"{self.CurrentIndex + 1}/{len(self.ImagePath)} — {os.path.basename(self.ImagePath[self.CurrentIndex])}"
            self.Load1_var.set(label)

        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            
            pil_img = self.load_image(path)
            self.orig_img = pil_img
            orig_width, orig_height = pil_img.size

            self.canvas.update_idletasks()  # Ensure canvas size is up to date
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()

            if orig_width > 0 and orig_height > 0:
                self.zoom_scale = min(canvas_w / orig_width, canvas_h / orig_height, 1.0)
            else:
                self.zoom_scale = 1.0

            self.fit_zoom_scale = self.zoom_scale  # store the minimum allowed zoom

            disp_w = int(orig_width * self.zoom_scale)
            disp_h = int(orig_height * self.zoom_scale)
            disp_img = pil_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            self.img = disp_img
            self.initial_display_img = disp_img.copy()
            self.img_tk = ImageTk.PhotoImage(disp_img)

            self.canvas.delete("all")
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()

            self.img_x = max((canvas_w - disp_w) // 2, 0)
            self.img_y = max((canvas_h - disp_h) // 2, 0)

            # Place image
            self.canvas.create_image(self.img_x, self.img_y, image=self.img_tk, anchor=tk.NW, tags="base_image")

            self.canvas.update_idletasks()  
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

            mask_png_path = os.path.splitext(path)[0] + "_mask.png"
            if os.path.exists(mask_png_path):
                mask_img = Image.open(mask_png_path).convert("L")
                mask_resized = mask_img.resize((disp_w, disp_h), Image.Resampling.NEAREST)
                self.mask_tk = ImageTk.PhotoImage(mask_resized)
                
            self.canvas.bind("<Motion>", self.show_pixel)
            self.points.clear()
            self.temp_line_ids.clear()
            self.temp_point_ids.clear()
            self.temp_shapes.clear()
            self.polygon_id.clear()
            self.new_shapes.clear()
            self.mask_data = None
            self.mask_visible = False
            self.tk_mask_overlay = None
            self.mask_overlay_id = None

            label_path = os.path.splitext(path)[0] + "_label.json"
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    data = json.load(f)
                    for shape in data.get("shapes", []):
                        if shape.get("shape_type") == "polygon":
                            points = shape.get("points", [])
                            pts_float = [(float(p[0]), float(p[1])) for p in points]
                            self.temp_shapes.append(pts_float)

                            if not any(len(pts_float) == len(s["points"]) and np.allclose(pts_float, s["points"]) for s in self.new_shapes):
                                self.new_shapes.append({
                                    "points": pts_float,
                                    "label": shape.get("label", "container")
                            })

            self.redraw_canvas()
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image:\n{e}")
            
        self.image_saved_once = False
        self.last_saved_format = None

    def show_pixel(self, event):
        if self.raw_np is None:
            self.coord_label.config(text="(0,0) Value=0")
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        img_x = int((canvas_x - self.img_x) / self.zoom_scale)
        img_y = int((canvas_y - self.img_y) / self.zoom_scale)
        
        try:
            h, w = self.raw_np.shape[:2]
            if 0 <= img_x < w and 0 <= img_y < h:
                val = self.raw_np[img_y, img_x]
                if isinstance(val, np.ndarray) or hasattr(val, '__len__'):
                    pixel_val = int(val[0]) if len(val) == 1 else int(val[0])
                else:
                    pixel_val = int(val)
                self.coord_label.config(text=f"({img_x},{img_y}) Value={pixel_val}")
            else:
                self.coord_label.config(text="(0,0) Value=0")
        except Exception:
            self.coord_label.config(text="(0,0) Value=0")


    def confirm_save_before_switch(self, direction):
    
        if self.shapes_modified and self.temp_shapes:
            result = messagebox.askquestion("Save Polygon?", "Do you want to save the polygon drawn?", icon='warning')
            if result == 'yes':
                self.savePressed(force=True)
            else:
            
                path = self.ImagePath[self.CurrentIndex]
                label_path = os.path.splitext(path)[0] + "_label.json"
                self.new_shapes.clear()
                self.temp_shapes.clear()
                if os.path.exists(label_path):
                    with open(label_path, "r") as f:
                        data = json.load(f)
                        for shape in data.get("shapes", []):
                            if shape.get("shape_type") == "polygon":
                                points = shape.get("points", [])
                                pts_float = [(float(p[0]), float(p[1])) for p in points]
                                self.temp_shapes.append(pts_float)
                                self.new_shapes.append({
                                    "points": pts_float,
                                    "label": shape.get("label", "container")
                                })
                self.shapes_modified = False

        if direction == "next":
            self.CurrentIndex = (self.CurrentIndex + 1) % len(self.ImagePath)
        elif direction == "prev":
            self.CurrentIndex = (self.CurrentIndex - 1) % len(self.ImagePath)

        self.showImagePaths()
        self.mode = "label"
        self.canvas.config(cursor="arrow")
        self.labellingPressed()

    def nextPressed(self):
        if self.ImagePath:
            self.confirm_save_before_switch("next")
        self.root.focus_set()


    def previousPressed(self):
        if self.ImagePath: 
            self.confirm_save_before_switch("prev")
            self.root.focus_set()

    def undoPressed(self, event=None):
        if self.mode == "edit":
            if self.edit_undo_stack:
                last = self.edit_undo_stack.pop()
                shape_index = last["shape_index"]
                shape = self.temp_shapes[shape_index]

                if last.get("inserted") is not None and last.get("removed") is None:
                    removed = shape.pop(last["segment_index"] + 1)
                    self.edit_redo_stack.append({
                        "shape_index": shape_index,
                        "segment_index": last["segment_index"],
                        "inserted": removed,
                        "removed": None
                    })

                elif last.get("removed") is not None and last.get("inserted") is None:
                    shape.insert(last["point_index"], last["removed"])
                    self.edit_redo_stack.append({
                        "shape_index": shape_index,
                        "point_index": last["point_index"],
                        "inserted": None,
                        "removed": last["removed"]
                    })

                self.shapes_modified = True
                self.redraw_canvas()
                self.canvas.unbind("<Button-1>")
                self.canvas.bind("<Button-1>", self.edit_click_handler)
            return  

        if self.mode == "label":
            if self.points:
                removed = self.points.pop()
                self.edit_redo_stack.append({
                    "action": "restore_point",
                    "point": removed
                })
                self.redraw_canvas()
            else:
                messagebox.showinfo("Undo", "No points to undo.")
         
    def redoPressed(self, event=None):
        if self.mode == "edit":
            if self.edit_redo_stack:
                last = self.edit_redo_stack.pop()
                shape_index = last["shape_index"]
                shape = self.temp_shapes[shape_index]

                if last.get("removed") is not None and last.get("inserted") is None:
                    point_index = last["point_index"]
                    if 0 <= point_index < len(shape):
                        removed = shape.pop(last["point_index"])
                        self.edit_undo_stack.append({
                            "shape_index": last["shape_index"],
                            "point_index": last["point_index"],
                            "inserted": None,
                            "removed": removed
                        })

                elif last.get("inserted") is not None and last.get("removed") is None:
                    
                    if "segment_index" in last:
                        insert_index = last["segment_index"] + 1
                    else:
                        insert_index = last["point_index"]
                    if 0 <= insert_index <= len(shape):
                        shape.insert(insert_index, last["inserted"])
                        self.edit_undo_stack.append({
                            "shape_index": shape_index,
                            "segment_index": last.get("segment_index", insert_index - 1),
                            "inserted": last["inserted"],
                            "removed": None
                        })

                self.shapes_modified = True
                self.redraw_canvas()
                self.canvas.unbind("<Button-1>")
                self.canvas.bind("<Button-1>", self.edit_click_handler)
                return

        if self.mode == "label" and self.edit_redo_stack:
            last = self.edit_redo_stack.pop()
            if last.get("action") == "restore_point":
                self.points.append(last["point"])
                self.edit_undo_stack.append({
                    "action": "restore_point",
                    "point": last["point"]
                })
                self.redraw_canvas()

    def fitWindowPressed(self):
        if not self.orig_img:
            return
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.orig_img.size

        scale_w = canvas_w / img_w
        scale_h = canvas_h / img_h
        fit_scale = min(scale_w, scale_h)

        self.zoom_scale = fit_scale

        new_w = int(img_w * self.zoom_scale)
        new_h = int(img_h * self.zoom_scale)

        self.img_x = max(0, (canvas_w - new_w) // 2)
        self.img_y = max(0, (canvas_h - new_h) // 2)

        self.redraw_canvas()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.root.focus_set()


    def _on_mouse_wheel(self, event):
        if hasattr(event, 'delta') and event.delta:        
            factor = 1.2 if event.delta > 0 else 1.0 / 1.2
        elif hasattr(event, 'num'):
            if event.num == 4:
                factor = 1.2
            elif event.num == 5:
                factor = 1.0 / 1.2
            else:
                return
        else:
            return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        self.zoom_at(factor, canvas_x, canvas_y)

    def enable_polygon_deletion(self):
        self.hover_highlight_id = None

        def on_motion(event):
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            overlapping = self.canvas.find_overlapping(cx, cy, cx, cy)

            if self.hover_highlight_id:
                self.canvas.delete(self.hover_highlight_id)
                self.hover_highlight_id = None

            for item in reversed(overlapping):
                if item in self.polygon_id:
                    index = self.polygon_id.index(item)
                    shape = self.temp_shapes[index]
                    screen_pts = [
                        (int(round(x * self.zoom_scale)) + self.img_x,
                        int(round(y * self.zoom_scale)) + self.img_y)
                        for (x, y) in shape]
                    flat = [coord for pt in screen_pts for coord in pt]
                    self.hover_highlight_id = self.canvas.create_polygon(
                        flat, fill="red", stipple="gray50", outline="", tags="hover_preview")
                    break

        def on_click(event):
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            overlapping = self.canvas.find_overlapping(cx, cy, cx, cy)

            for item in reversed(overlapping):
                if item in self.polygon_id:
                    index = self.polygon_id.index(item)
                    deleted_shape = self.temp_shapes[index]

                    self.edit_undo_stack.append({
                        "action": "delete_polygon",
                        "temp_shapes": [shape.copy() for shape in self.temp_shapes],
                        "polygon_id": self.polygon_id.copy(),
                        "new_shapes": self.new_shapes.copy()
                    })

                    self.canvas.delete(item)
                    del self.polygon_id[index]
                    del self.temp_shapes[index]

                    self.new_shapes = [
                        shape for shape in self.new_shapes
                        if not (
                            len(shape["points"]) == len(deleted_shape) and
                            all(np.allclose(p1, p2) for p1, p2 in zip(shape["points"], deleted_shape))
                        )
                    ]

                    self.shapes_modified = True
                    self.redraw_canvas()
                    break

            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<Button-1>")
            if self.hover_highlight_id:
                self.canvas.delete(self.hover_highlight_id)
                self.hover_highlight_id = None
            self.mode = "label"
            self.canvas.config(cursor="arrow")
            self.labellingPressed()

        self.canvas.bind("<Motion>", on_motion)
        self.canvas.bind("<Button-1>", on_click)

    def update_dat_file(self):
        if not self.ImagePath:
            return
        image_path = self.ImagePath[self.CurrentIndex]
        msk_path = os.path.splitext(image_path)[0] + "_label.dat"
        orig_w, orig_h = self.orig_img.size
        mask = np.zeros((orig_w, orig_h), dtype=np.uint8)
        for shape_dict in self.new_shapes:
            shape = shape_dict["points"]
            pts = np.array([[int(round(y)), int(round(x))] for x, y in shape], dtype=np.int32)
            if pts.size == 0:
                continue
            cv2.fillPoly(mask, [pts], 255)
        with open(msk_path, "wb") as f:
            f.write(struct.pack('II', orig_h, orig_w))
            f.write(mask.tobytes())

        if self.show_mask_var.get():
            try:
                png_path = os.path.splitext(image_path)[0] + "_mask.png"
                img = Image.fromarray(mask.T)  # L mode
                img.save(png_path)
            except Exception as e:
                print("Failed to save PNG:", e)

    def deletePressed(self):
        self.mode = "delete"
        self.enable_polygon_deletion()
        self.root.focus_set()

        
    def render_overlays(self):
        self.canvas.delete("polygon")
        self.canvas.delete("temp_point")
        self.canvas.delete("temp_line")
        self.canvas.delete("edit_point")  

        self.polygon_id.clear()
        for shape in self.temp_shapes:
            screen_pts = [
                (int(round(x * self.zoom_scale)) + self.img_x,
                int(round(y * self.zoom_scale)) + self.img_y)
                for (x, y) in shape
            ]
            flat = [coord for pt in screen_pts for coord in pt]
            polygon_id = self.canvas.create_polygon(flat, outline="red", fill='', width=2, tags="polygon")
            self.polygon_id.append(polygon_id)

            if self.mode == "edit":
                for sx, sy in screen_pts:
                    self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="red", tags="edit_point")

        for i, point in enumerate(self.points):
            sx = int(round(point[0] * self.zoom_scale)) + self.img_x
            sy = int(round(point[1] * self.zoom_scale)) + self.img_y
            self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="red", tags="temp_point")

            if i > 0:
                prev = self.points[i-1]
                px = int(round(prev[0] * self.zoom_scale)) + self.img_x
                py = int(round(prev[1] * self.zoom_scale)) + self.img_y
                self.canvas.create_line(px, py, sx, sy, fill="red", width=2, tags="temp_line")

    
        if self.mask_visible and self.mask_data is not None:
            h, w = self.mask_data.shape
            visible_mask = np.where(self.mask_data > 0, 255, 0).astype(np.uint8)
            mask_img = Image.fromarray(visible_mask).convert("L")
            scaled_mask = mask_img.resize((int(w * self.zoom_scale), int(h * self.zoom_scale)), Image.Resampling.NEAREST)
            self.tk_mask_overlay = ImageTk.PhotoImage(scaled_mask)
            if self.mask_overlay_id is not None:
                self.canvas.delete(self.mask_overlay_id)
            self.mask_overlay_id = self.canvas.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.tk_mask_overlay)

            
    def render_image(self):
        if self.orig_img is None:
            return

        brightness = self.brightness_var.get()
        contrast = self.contrast_var.get()

        img_np = np.array(self.orig_img).astype(np.float32)
        img_np = img_np * contrast + (brightness - 1.0) * 128
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)

        adjusted_img = Image.fromarray(img_np)

        disp_w = int(adjusted_img.size[0] * self.zoom_scale)
        disp_h = int(adjusted_img.size[1] * self.zoom_scale)
        disp_img = adjusted_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

        self.img = disp_img
        self.img_tk = ImageTk.PhotoImage(disp_img)

        self.canvas.delete("base_image")
        self.canvas.create_image(self.img_x, self.img_y, image=self.img_tk, anchor=tk.NW, tags="base_image")
        self.canvas.delete("Prev")
        
    def redraw_canvas(self):
        self.render_image()
        self.render_overlays()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def save_annotated_image(self, image_path, shapes):
        annotated_img = self.orig_img.copy()
        draw = ImageDraw.Draw(annotated_img)
        for shape in shapes:
            draw.polygon(shape, outline="red")
        annotated_path = os.path.splitext(image_path)[0] + "_labelled.png"
        annotated_img.save(annotated_path)

    def save_dat_file(self, image_path, shapes=None,saved_formats=None):
        if shapes is None:
            shapes = self.new_shapes
        if not shapes:
            print("No polygons to save in DAT.")
            return
        if saved_formats is not None:
            saved_formats.append("Dat")

        orig_w, orig_h = self.orig_img.size
        mask = np.zeros((orig_w, orig_h), dtype=np.uint8)

        for shape_dict in shapes:
            shape = shape_dict["points"]
            pts = np.array([[int(round(y)), int(round(x))] for x, y in shape], dtype=np.int32)
            if pts.size == 0:
                continue
            cv2.fillPoly(mask, [pts], 255)

        msk_path = os.path.splitext(image_path)[0] + "_label.dat"
        with open(msk_path, "wb") as f:
            f.write(struct.pack('II', orig_h, orig_w))
            f.write(mask.tobytes())

        if self.show_mask_var.get():
            try:
                png_path = os.path.splitext(image_path)[0] + "_mask.png"
                img = Image.fromarray(mask.T)
                img.save(png_path)
                if saved_formats is not None:
                    saved_formats.append("PNG")
            except Exception as e:
                print("Failed to save PNG:", e)

    def enable_click_to_zoom(self):
        def zoom_in(event):
            self.zoom_at(1.2, event.x, event.y)
        def zoom_out(event):
            self.zoom_at(1.0 / 1.2, event.x, event.y)
        self.canvas.bind("<Control-Button-1>", zoom_in)
        self.canvas.bind("<Control-Button-3>", zoom_out)
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

    def view_msk_file(self, msk_path):
        if not os.path.exists(msk_path):
            messagebox.showerror("Missing", f"File not found:\n{msk_path}")
            return
        with open(msk_path, "rb") as f:
            header = f.read(8)
            h, w = struct.unpack('II', header)
            data = f.read()
            mask = np.frombuffer(data, dtype=np.uint8).reshape((w,h))
        cv2.imshow("Mask File", mask)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def zoomInPressed(self):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        center_x = canvas_w // 2
        center_y = canvas_h // 2
        self.zoom_at(1.2, center_x, center_y)
        self.root.focus_set()

        
    def zoomOutPressed(self):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        center_x = canvas_w // 2
        center_y = canvas_h // 2
        self.zoom_at(1.0 / 1.2, center_x, center_y)
        self.root.focus_set()


    def zoom_at(self, factor, screen_x, screen_y):
        if self.orig_img is None:
            return
        old_zoom = self.zoom_scale
        new_zoom = old_zoom * factor
        min_allowed_zoom = max(self.fit_zoom_scale, self.min_zoom)
        new_zoom = max(min_allowed_zoom, min(self.max_zoom, new_zoom))

        if abs(new_zoom - old_zoom) < 1e-4:
            return
        img_x = (screen_x - self.img_x) / old_zoom
        img_y = (screen_y - self.img_y) / old_zoom
        self.zoom_scale = new_zoom
        disp_w = int(self.orig_img.size[0] * self.zoom_scale)
        disp_h = int(self.orig_img.size[1] * self.zoom_scale)

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        self.img_x = int(screen_x - img_x * self.zoom_scale)
        self.img_y = int(screen_y - img_y * self.zoom_scale)

        self.img_x = max(min(self.img_x, canvas_w - 10), -disp_w + 10)
        self.img_y = max(min(self.img_y, canvas_h - 10), -disp_h + 10)

        self.redraw_canvas()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
    def enable_drag_zoom(self):
        self.canvas.config(cursor="tcross")
        self.canvas.bind("<Button-1>", self.start_zoom_rect)
        self.canvas.bind("<B1-Motion>", self.draw_zoom_rect)
        self.canvas.bind("<ButtonRelease-1>", self.finish_zoom_rect)
    
    def activate_intensive_zoom(self):
        self.intensive_zoom_mode = True
        self.canvas.config(cursor="tcross")
        self.canvas.bind("<Button-1>", self.start_zoom_rect)
        self.canvas.bind("<B1-Motion>", self.draw_zoom_rect)
        self.canvas.bind("<ButtonRelease-1>", self.finish_zoom_rect)
            
    def start_zoom_rect(self, event):
        self.zoom_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self.zoom_rect_id:
            self.canvas.delete(self.zoom_rect_id)
        self.zoom_rect_id = self.canvas.create_rectangle(*self.zoom_start, *self.zoom_start, outline="green", dash=(4, 2))

    def draw_zoom_rect(self, event):
        if self.zoom_start and self.zoom_rect_id:
            x0, y0 = self.zoom_start
            x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.coords(self.zoom_rect_id, x0, y0, x1, y1)

    def finish_zoom_rect(self, event):
        if not self.zoom_start or not self.zoom_rect_id:
            return

        x0, y0 = self.zoom_start
        x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(self.zoom_rect_id)
        self.zoom_rect_id = None
        self.zoom_start = None

        x_min, x_max = sorted([x0, x1])
        y_min, y_max = sorted([y0, y1])
        region_w = x_max - x_min
        region_h = y_max - y_min
        if region_w < 30 or region_h < 30:
            return  # too small to zoom

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.orig_img.size
        img_disp_w = img_w * self.zoom_scale
        img_disp_h = img_h * self.zoom_scale

        fraction_x = region_w / img_disp_w
        fraction_y = region_h / img_disp_h
        fraction = max(fraction_x, fraction_y)

        target_zoom = self.zoom_scale / math.sqrt(fraction)
        new_zoom = max(self.min_zoom, min(self.max_zoom, target_zoom))

        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2

        self.zoom_at(new_zoom / self.zoom_scale, center_x, center_y)

        self.intensive_zoom_mode = False
        self.canvas.config(cursor="arrow")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        if self.mode == "label":
            self.labellingPressed()

    def show_dat_file(self, event=None):
        if not self.ImagePath:
            self._prepare_mask_release()
            self.root.after(10, lambda: messagebox.showerror("Missing", "No Dat file found for current image"))
            return
        image_path = self.ImagePath[self.CurrentIndex]
        msk_path = os.path.splitext(image_path)[0] + "_label.dat"
        if not os.path.exists(msk_path):
            self._prepare_mask_release()
            self.root.after(10, lambda: messagebox.showerror("Missing", "No Dat file found for current image"))
            return

        '''if getattr(self, "mask_visible", False):
            if hasattr(self, "mask_overlay_id") and self.mask_overlay_id is not None:
                self.canvas.delete(self.mask_overlay_id)
            self.mask_visible = False
            return'''

        with open(msk_path, "rb") as f:
            header = f.read(8)
            h, w = struct.unpack('II', header)
            data = f.read()
            mask = np.frombuffer(data, dtype=np.uint8).reshape((w, h))

        self.mask_data = mask
        self.mask_visible = True
    
        orig_w, orig_h = self.orig_img.size
        disp_w = int(orig_w * self.zoom_scale)
        disp_h = int(orig_h * self.zoom_scale)
        visible_mask = np.where(mask > 0, 255, 0).astype(np.uint8)
        mask_img = Image.fromarray(visible_mask.T).convert("L")
        mask_img = mask_img.resize((disp_w, disp_h), Image.Resampling.NEAREST)
        self.tk_mask_overlay = ImageTk.PhotoImage(mask_img)
        
        if self.mask_overlay_id is not None:
            self.canvas.delete(self.mask_overlay_id)
        self.mask_overlay_id = self.canvas.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.tk_mask_overlay)

    def close_msk_file(self, event=None):
        if self.mask_overlay_id is not None:
            self.canvas.delete(self.mask_overlay_id)
            self.mask_overlay_id = None
        self.mask_visible = False
        
    def _prepare_mask_release(self):
        self.mask_visible = True
        if self.mask_overlay_id is None:
            self.mask_overlay_id = self.canvas.create_rectangle(0, 0, 1, 1, state="hidden")

    def show_msk_pressed(self):
        if self.orig_img is None or self.mask_data is None:
            return
        self.zoom_scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.redraw_canvas()
        self.draw_mask_overlay()

    def draw_mask_overlay(self):
        if self.mask_data is None or self.orig_img is None:
            return
        orig_w, orig_h = self.orig_img.size
        scaled_w = int(orig_w * self.zoom_scale)
        scaled_h = int(orig_h * self.zoom_scale)
        mask_img = Image.fromarray((self.mask_data * 255).astype(np.uint8)).convert("L")
        mask_img = mask_img.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)
        self.tk_mask_overlay = ImageTk.PhotoImage(mask_img)
        if hasattr(self, "mask_overlay_id") and self.mask_overlay_id is not None:
            self.canvas.delete(self.mask_overlay_id)
        self.mask_overlay_id = self.canvas.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.tk_mask_overlay)
        self.mask_visible = True

    def labellingPressed(self):
        if self.mode != "label":
            return
        def on_left_click(event):
            
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            img_x = (canvas_x - self.img_x) / self.zoom_scale
            img_y = (canvas_y - self.img_y) / self.zoom_scale

            orig_w, orig_h = self.orig_img.size
            if not (0 <= img_x < orig_w and 0 <= img_y < orig_h):
                return  
            self.points.append((img_x, img_y))
            self.edit_redo_stack.clear()
            sx = int(round(img_x * self.zoom_scale)) + self.img_x
            sy = int(round(img_y * self.zoom_scale)) + self.img_y
            point_id = self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="red",tags="temp_point")
            self.temp_point_ids.append(point_id)

            if len(self.points) > 1:
                prev = self.points[-2]
                px = int(round(prev[0] * self.zoom_scale)) + self.img_x
                py = int(round(prev[1] * self.zoom_scale)) + self.img_y
                line_id = self.canvas.create_line(px, py, sx, sy, fill="red", width=2,tags="temp_line")
                self.temp_line_ids.append(line_id)
                

        def on_right_click(event):
            if len(self.points) < 3:
                messagebox.showinfo("Polygon Error", "Need at least 3 points to form a polygon.")
                return
            labels = self.load_labels_from_csv(r"C:\Users\kgopidesi\Downloads\labels.csv")
            if not labels:
                messagebox.showerror("Label Error", "No labels found in CSV.")
                return

            pts_float = [(float(x), float(y)) for x, y in self.points]
            screen_pts = [
                (int(round(x * self.zoom_scale)) + self.img_x,
                int(round(y * self.zoom_scale)) + self.img_y)
                for (x, y) in pts_float
            ]
            flat = [coord for pt in screen_pts for coord in pt]
            polygon_id = self.canvas.create_polygon(flat, outline="red", fill='', width=2, tags="polygon")
            self.polygon_id.append(polygon_id)

            popup = tk.Toplevel(self.root)
            self.label_popup_open = True
            self.label_popup_ref = popup
            popup.title("Select Label")
            popup.geometry("250x150")
            popup.transient(self.root)
            popup.grab_set()

            screen_w = popup.winfo_screenwidth()
            screen_h = popup.winfo_screenheight()
            popup.geometry(f"+{screen_w//2 - 125}+{screen_h//2 - 75}")

            tk.Label(popup, text="Choose label:").pack(pady=5)

            selected_label = tk.StringVar(value=labels[0])
            dropdown = ttk.Combobox(popup, textvariable=selected_label, values=labels, state="readonly")
            dropdown.pack(pady=5)

            def save_label():
                self.label_popup_open = False
                self.label_popup_ref = None
                self._save_polygon_with_label(selected_label.get(), popup)

            def cancel_label():
                self.label_popup_open = False
                self.label_popup_ref = None
                self._save_polygon_with_label("No Label", popup)
                self.show_temp_message("Polygon saved as 'No Label'")

            def on_popup_close():
                self.label_popup_open = False
                self.label_popup_ref = None
                self._save_polygon_with_label("No Label", popup)
                self.show_temp_message("Polygon saved as 'No Label'")

            popup.protocol("WM_DELETE_WINDOW", on_popup_close)

            btn_frame = tk.Frame(popup)
            btn_frame.pack(pady=10)

            tk.Button(btn_frame, text="Save", command=save_label).pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=cancel_label).pack(side="right", padx=10)


        self.canvas.bind("<Button-1>", on_left_click)
        self.canvas.bind("<Button-3>", on_right_click)
        self.root.focus_set()
        
    def handle_s_key(self, event=None):
        if self.label_popup_open and self.label_popup_ref:
            for widget in self.label_popup_ref.winfo_children():
                if isinstance(widget, tk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, tk.Button) and btn.cget("text") == "Save":
                            btn.invoke()
                            return
        else:
            self.savePressed()

    def show_temp_message(self, text):
        msg_popup = tk.Toplevel(self.root)
        msg_popup.title("Info")
        msg_popup.geometry("250x100")
        msg_popup.transient(self.root)
        msg_popup.grab_set()

        screen_w = msg_popup.winfo_screenwidth()
        screen_h = msg_popup.winfo_screenheight()
        msg_popup.geometry(f"+{screen_w//2 - 125}+{screen_h//2 - 50}")

        tk.Label(msg_popup, text=text, font=("Arial", 10)).pack(expand=True)
        msg_popup.after(1500, msg_popup.destroy)
           
    def _save_polygon_with_label(self, label, popup):
        pts_float = [(float(x), float(y)) for x, y in self.points]
        self.temp_shapes.append(pts_float)
        self.edit_undo_stack.append({
        "action": "add_polygon",
        "shape": pts_float
        })
        self.edit_redo_stack.clear()
        self.new_shapes.append({
            "points": pts_float,
            "label": label
        })
        self.shapes_modified = True
        self.redraw_canvas()
        self.points.clear()
        for line_id in self.temp_line_ids:
            self.canvas.delete(line_id)
        for point_id in self.temp_point_ids:
            self.canvas.delete(point_id)
        self.temp_line_ids.clear()
        self.temp_point_ids.clear()
        popup.destroy()
        
        if self.mode == "label":
            self.labellingPressed()
    def update_image(self, value=None):
        if self.orig_img is None:
            return

        try:
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()
            raw_gamma = self.gamma_var.get()
            gamma = 0.1 + 4.9 * ((raw_gamma - 0.1) / 1.9) ** 2

            img = self.orig_img.convert("RGB")
            img_np = np.array(img).astype(np.float32)

            img_np = img_np * contrast + (brightness - 1.0) * 128
            img_np = np.clip(img_np, 0, 255)
            img_np /= 255.0
            img_np = np.power(img_np, gamma)
            img_np *= 255.0
            img_np = np.clip(img_np, 0, 255)
            img_np = img_np.astype(np.uint8)

            adjusted_img = Image.fromarray(img_np)
            disp_w = int(adjusted_img.size[0] * self.zoom_scale)
            disp_h = int(adjusted_img.size[1] * self.zoom_scale)
            disp_img = adjusted_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

            self.img = disp_img
            self.img_tk = ImageTk.PhotoImage(disp_img)

            self.canvas.delete("base_image")
            self.canvas.create_image(self.img_x, self.img_y, image=self.img_tk, anchor=tk.NW, tags="base_image")
            self.render_overlays()
        except Exception as e:
            print("Update image failed:", e)

    def reset_brightness_contrast(self):
        if self.initial_display_img:
            self.img = self.initial_display_img.copy()
            self.img_tk = ImageTk.PhotoImage(self.img)
            self.canvas.delete("base_image")
            self.canvas.create_image(self.img_x, self.img_y, image=self.img_tk, anchor=tk.NW, tags="base_image")
            self.render_overlays()
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.gamma_var.set(1.0)

   
        self.points.clear()
        for line_id in self.temp_line_ids:
            self.canvas.delete(line_id)
        for point_id in self.temp_point_ids:
            self.canvas.delete(point_id)
        self.temp_line_ids.clear()
        self.temp_point_ids.clear()

    def savePressed(self, force=False):
        image_path = self.ImagePath[self.CurrentIndex]
        base_name, extension = os.path.splitext(image_path)
        selected_format = self.formatSelector.get()

        if not self.temp_shapes:
            self.show_temp_message("No annotations found. Nothing saved.")

            for ext in ("_label.json", "_label.dat", "_mask.png"):
                file_path = base_name + ext
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Failed to delete {file_path}:", e)
            return

        if selected_format == "json":
            dat_path = base_name + "_label.dat"
            if os.path.exists(dat_path):
                try:
                    os.remove(dat_path)
                except Exception as e:
                    print("Failed to delete DAT file:", e)

        format_changed = (self.last_saved_format != selected_format)
        png_flag_changed = self.last_saved_png_flag != bool(self.show_mask_var.get())

        if not self.shapes_modified and not force and not format_changed and not png_flag_changed:
            self.last_saved_format = selected_format
            self.last_saved_png_flag = bool(self.show_mask_var.get())
            return


        orig_w, orig_h = self.orig_img.size
        all_shapes = []
        for shape in self.temp_shapes:
            matched_shape = next(
                (s for s in self.new_shapes if len(shape) == len(s["points"]) and np.allclose(shape, s["points"])), None)
            label = matched_shape["label"] if matched_shape else "container"
            all_shapes.append({
                "points": shape,
                "label": label
            })

        saved_formats = []

        if selected_format in ("json", "both"):
            save_path = base_name + "_label.json"
            data = {
                "version": "1.0.0",
                "shapes": [],
                "imagePath": os.path.basename(image_path),
                "imageData": None,
                "imageHeight": orig_h,
                "imageWidth": orig_w
            }

            for shape_data in all_shapes:
                shape = {
                    "label": shape_data["label"],
                    "points": [[int(round(x)), int(round(y))] for x, y in shape_data["points"]],
                    "group_id": None,
                    "description": "",
                    "shape_type": "polygon",
                    "mask": None
                }
                data["shapes"].append(shape)

            with open(save_path, "w") as file:
                json.dump(data, file, indent=4)
            saved_formats.append("Json")

        if selected_format in ("dat", "both"):
            self.save_dat_file(image_path, all_shapes, saved_formats)
            saved_formats.append("Dat")

        self.new_shapes = all_shapes.copy()
        self.shapes_modified = False
        self.mode = "label"
        self.canvas.config(cursor="arrow")
        self.labellingPressed()

        if not self.image_saved_once:
            main_formats = [fmt for fmt in saved_formats if fmt != "PNG"]
            msg = "ALL polygons are saved in " + " & ".join(main_formats) + " file" + ("s" if len(main_formats) > 1 else "")
            msg += "\nDAT is saved as PNG also" if "PNG" in saved_formats else ""
            self.image_saved_once = True
        else:
            msg = "Changes are Updated"

        for i, var in enumerate(self.dropdown_vars):
            index, path, _ = self.dropdown_items[i]
            is_labeled = self.is_image_labeled(path)
            var.set(1 if is_labeled else 0)
            self.dropdown_items[i] = (index, path, is_labeled)

        if self.dropdown_popup and self.dropdown_popup.winfo_exists():
            self.dropdown_popup.destroy()
            self.open_dropdown()

        self.show_temp_message(msg)
        self.last_saved_format = selected_format
        self.last_saved_png_flag = bool(self.show_mask_var.get())
        self.root.focus_set()
   
    def is_image_labeled(self,path):
        base = os.path.splitext(path)[0]
        json_path = base + "_label.json"
        dat_path = base + "_label.dat"
        return os.path.exists(json_path) or os.path.exists(dat_path)

        
    def convert_json_to_txt(self):
        if not self.ImagePath:
            self.show_temp_message("No image loaded")
            return

        image_path = self.ImagePath[self.CurrentIndex]
        base_name = os.path.splitext(image_path)[0]
        json_path = base_name + "_label.json"
        txt_path = base_name + "_label.txt"

        if not os.path.exists(json_path):
            self.show_temp_message("JSON file not found")
            return

        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            shapes = [s for s in data.get("shapes", []) if s.get("shape_type") == "polygon" and s.get("points")]
            lines = [str(len(shapes))]

            for count, shape in enumerate(shapes, start=1):
                points = shape["points"]
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x_min = int(round(min(xs)))
                y_min = int(round(min(ys)))
                x_max = int(round(max(xs)))
                y_max = int(round(max(ys)))

                lines.extend([str(x_min), str(y_min), str(x_max), str(y_max), ""])

            with open(txt_path, "w") as f:
                f.write("\n".join(lines))
            self.show_temp_message("TXT file saved with bounding boxes")

        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert JSON to TXT:\n{e}")


    def convert_json_to_cargomarkerxml(self):
        if not self.ImagePath:
            self.show_temp_message("No image loaded")
            return

        image_path = self.ImagePath[self.CurrentIndex]
        base_name = os.path.splitext(image_path)[0]
        json_path = base_name + "_label.json"
        xml_path = base_name + ".cargomarker"

        if not os.path.exists(json_path):
            self.show_temp_message("JSON file not found")
            return

        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            xml_lines = []

            for shape in data.get("shapes", []):
                if shape.get("shape_type") == "polygon":
                    points = shape.get("points", [])
                    if not points:
                        continue
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    x_min = int(round(min(xs)))
                    y_min = int(round(min(ys)))
                    x_max = int(round(max(xs)))
                    y_max = int(round(max(ys)))

                    xml_lines.append('<shape type="rectangle">')
                    xml_lines.append('  <color value="#ff0000"/>')
                    xml_lines.append(f'  <rect left="{x_min}" top="{y_min}" right="{x_max}" bottom="{y_max}"/>')
                    xml_lines.append('  <text value="BULK"/>')
                    xml_lines.append('</shape>')

            if xml_lines:
                with open(xml_path, "w") as f:
                    f.write("\n".join(xml_lines))
                self.show_temp_message("CargoMarker XML saved")
            else:
                self.show_temp_message("No valid polygons found in JSON")

        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert JSON to CargoMarker XML:\n{e}")

    def convert_json_to_dat(self):
        if not self.ImagePath:
            self.show_temp_message("No image loaded")
            return

        image_path = self.ImagePath[self.CurrentIndex]
        base_name = os.path.splitext(image_path)[0]
        json_path = base_name + "_label.json"
        dat_path = base_name + "_label.dat"

        if not os.path.exists(json_path):
            self.show_temp_message("JSON file not found")
            return

        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            orig_w, orig_h = self.orig_img.size
            mask = np.zeros((orig_w, orig_h), dtype=np.uint8)

            for shape in data.get("shapes", []):
                if shape.get("shape_type") == "polygon":
                    points = shape.get("points", [])
                    pts = np.array([[int(round(y)), int(round(x))] for x, y in points], dtype=np.int32)
                    if pts.size > 0:
                        cv2.fillPoly(mask, [pts], 255)

            with open(dat_path, "wb") as f:
                f.write(struct.pack('II', orig_h, orig_w))
                f.write(mask.tobytes())

            if self.show_mask_var.get():
                try:
                    png_path = base_name + "_mask.png"
                    img = Image.fromarray(mask.T)
                    img.save(png_path)
                    self.show_temp_message("DAT and PNG saved from JSON")
                except Exception as e:
                    print("Failed to save PNG:", e)
            else:
                self.show_temp_message("DAT file saved from JSON")

        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert JSON to DAT:\n{e}")

    def show_convert_options(self):
        popup = tk.Toplevel(self.root)
        popup.title("Convert JSON to Format")
        popup.geometry("300x200")
        popup.transient(self.root)
        popup.grab_set()

        popup.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        popup_w = popup.winfo_width()
        popup_h = popup.winfo_height()
        
        x = root_x + root_w - popup_w - 20
        y = root_y + root_h - popup_h - 40
        
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="Choose conversion format:", font=("Arial", 12)).pack(pady=10)

        options = [
            ("JSON to .txt", self.convert_json_to_txt),
            ("JSON to .cargomarkerxml", self.convert_json_to_cargomarkerxml),
            ("Json to .dat", self.convert_json_to_dat)
        ]

        for label, func in options:
            tk.Button(popup, text=label, width=25, command=lambda f=func, p=popup: (f(), p.destroy())).pack(pady=5)

if __name__ == "__main__":
    Load_file()
