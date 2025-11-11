import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk, ImageDraw
import json
import struct
import numpy as np
import cv2
import scipy.ndimage
import threading
from collections import OrderedDict

# ----------------- Small LRU cache for decoded PIL images -----------------
class ImageLRU:
    def __init__(self, capacity=8):
        self.capacity = capacity
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def put(self, key, value):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)

# ----------------- App -----------------
class Load_file:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Loader")
        self.root.state('zoomed')

        self.ImagePath = []
        self.CurrentIndex = 0
        self.labelling = 0
        self.points = []
        self.polygon_id = []
        self.temp_shapes = []     # list of polygons in original image coords (floats)
        self.redo_stack = []
        self.new_shapes = []
        self.shapes_modified = False
        self.temp_line_ids = []
        self.temp_point_ids = []
        self.orig_img = None      # PIL original image (unscaled, 8-bit RGB)
        self.img = None           # current displayed (scaled) PIL image
        self.img_tk = None
        self.mask_data = None
        self.mask_visible = False
        self.mask_overlay_id = None
        self.tk_mask_overlay = None
        self.img_x = 0
        self.img_y = 0
        self.mode = "label"

        # Zoom/pan
        self.zoom_scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.min_zoom = 0.1
        self.max_zoom = 8.0

        # Cache for decoded, 8-bit RGB PIL images
        self.cache = ImageLRU(capacity=10)

        # Build UI
        self.top_frame = tk.Frame(self.root, bg="white")
        self.top_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.root, bg="lightgray")
        self.bottom_frame.pack(side="bottom", fill="x")

        self.canvas_frame = tk.Frame(self.top_frame)
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.contrast_var = tk.DoubleVar(value=1.0)

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

        # Bottom controls
        self.Listfile = tk.Label(self.bottom_frame, text="List File:")
        self.Listfile.grid(row=0, column=0, padx=0, pady=0)

        self.Load1 = tk.Entry(self.bottom_frame, width=25)
        self.Load1.grid(row=0, column=1, padx=0, pady=0)

        self.Browse = tk.Button(self.bottom_frame, text=" Browse ", command=self.browsePressed)
        self.Browse.grid(row=0, column=2, padx=10, pady=10)

        self.NumberShowing = tk.Entry(self.bottom_frame, width=8)
        self.NumberShowing.grid(row=1, column=0, padx=10, pady=10)

        self.InsidePath = tk.Entry(self.bottom_frame, width=25)
        self.InsidePath.grid(row=1, column=1, padx=10, pady=10)

        self.Previous = tk.Button(self.bottom_frame, text="Previous", command=self.previousPressed)
        self.Previous.grid(row=1, column=2, padx=10, pady=10)

        self.Next = tk.Button(self.bottom_frame, text="Next", command=self.nextPressed)
        self.Next.grid(row=1, column=3, padx=0, pady=0)

        self.save = tk.Button(self.bottom_frame ,text="Save", command=self.savePressed)
        self.save.grid(row=0, column=9, padx=10, pady=10)

        self.coord_label = tk.Label(self.bottom_frame, text="X: 0, Y: 0", width=25, height=2, font=("Bold",10))
        self.coord_label.grid(row=2, column=0,columnspan=2, padx=5, pady=5)
        
        self.reset_btn = tk.Button(self.bottom_frame, text="Reset", command=self.reset_brightness_contrast)
        self.reset_btn.grid(row=1, column=6, columnspan=2, padx=0, pady=2)

        # Brightness label and slider
        brightness_frame = tk.Frame(self.bottom_frame)
        brightness_frame.grid(row=1, column=4, columnspan=4, sticky="w", padx=10, pady=2)

        tk.Label(brightness_frame, text="Brightness", width=10, anchor="w").pack(side="left")
        tk.Button(brightness_frame, text="◀", width=2, command=lambda: self.adjust_brightness(-0.1)).pack(side="left")
        tk.Scale(brightness_frame, from_=0.0, to=2.0, resolution=0.1, orient="horizontal",
         variable=self.brightness_var, command=self.update_image, length=200).pack(side="left")
        tk.Button(brightness_frame, text="▶", width=2, command=lambda: self.adjust_brightness(0.1)).pack(side="left")

        contrast_frame = tk.Frame(self.bottom_frame)
        contrast_frame.grid(row=2, column=4, columnspan=4, sticky="w", padx=10, pady=2)

        tk.Label(contrast_frame, text="Contrast", width=10, anchor="w").pack(side="left")
        tk.Button(contrast_frame, text="◀", width=2, command=lambda: self.adjust_contrast(-0.1)).pack(side="left")
        tk.Scale(contrast_frame, from_=0.0, to=2.0, resolution=0.1, orient="horizontal",
         variable=self.contrast_var, command=self.update_image, length=200).pack(side="left")
        tk.Button(contrast_frame, text="▶", width=2, command=lambda: self.adjust_contrast(0.1)).pack(side="left")

        self.Labeling = tk.Button(self.bottom_frame, text="Start labelling", command=self.labellingPressed)
        self.Labeling.grid(row=0, column=8, padx=10, pady=10)

        self.Undo = tk.Button(self.bottom_frame, text="Undo", command=self.undoPressed)
        self.Undo.grid(row=2, column=8, padx=10, pady=10)
        
        self.fitWindow=tk.Button(self.bottom_frame,text="Fit Window",command=self.fitWindowPressed)
        self.fitWindow.grid(row=0,column=12 ,padx=10,pady=10)

        self.Delete = tk.Button(self.bottom_frame, text="Delete", command=self.deletePressed)
        self.Delete.grid(row=2, column=9, padx=10, pady=10)

        self.formatSelector = tk.StringVar(value="json")
        self.json = tk.Radiobutton(self.bottom_frame, text="  Json   ", variable=self.formatSelector, value="json")
        self.json.grid(row=0, column=10, padx=10, pady=10)
        
        self.both = tk.Radiobutton(self.bottom_frame, text="Json & MSK", variable=self.formatSelector, value="both")
        self.both.grid(row=1, column=10, padx=10, pady=10)

        self.ShowMaskFile = tk.Button(self.bottom_frame, text="Show_MSk_File")
        self.ShowMaskFile.grid(row=1, column=12, padx=10, pady=10)
        self.ShowMaskFile.bind("<ButtonPress-1>", self.show_msk_file)
        self.ShowMaskFile.bind("<ButtonRelease-1>", self.close_msk_file)
        
        self.show_mask_var = tk.IntVar(value=False)
        self.mask_checkbox = tk.Checkbutton(self.bottom_frame, text="Save MSK", variable=self.show_mask_var)
        self.mask_checkbox.grid(row=1, column=9, padx=10, pady=10)

        self.zoomin = tk.Button(self.bottom_frame, text="Zoom_in", command=self.zoomInPressed)
        self.zoomin.grid(row=2, column=10,padx=0,pady=0)

        self.zoomout = tk.Button(self.bottom_frame, text="Zoom_out", command=self.zoomOutPressed)
        self.zoomout.grid(row=2, column=11,padx=0,pady=0)
        
        self.toggle_mode_btn = tk.Button(self.bottom_frame, text="🖐️Palm Mode", command=self.toggle_mode)
        self.toggle_mode_btn.grid(row=1, column=13, padx=10, pady=5)
    
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        self.root.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 * int(e.delta / 120), "units"))
        self.root.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux scroll up
        self.root.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))   # Linux scroll down
        self.root.bind("<Delete>", lambda event: self.undoPressed())
        
        self.root.mainloop()

    # ----------------- UI callbacks -----------------
    def browsePressed(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")], title="Select a .txt file")
        if file_path:
            self.Load1.delete(0, tk.END)
            self.Load1.insert(0, file_path)
        path = self.Load1.get().strip()
        if not path.endswith(".txt"):
            messagebox.showerror("Invalid", "Select only .txt file")
            return
        try:
            self.ImagePath.clear()
            with open(path, "r") as f:
                lines = f.read().splitlines()
                for line in lines:
                    stripped = line.strip().strip('"')
                    if stripped.lower().endswith(('.jpg','.png','.jpeg','.cargoimage','.img')) and os.path.exists(stripped):
                        self.ImagePath.append(stripped)
            if self.ImagePath:
                self.CurrentIndex = 0
                self.showImagePaths()
            else:
                messagebox.showerror("Empty File", "No valid image paths found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

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
        else:
            self.mode = "label"
            self.canvas.config(cursor="arrow")
            self.toggle_mode_btn.config(text="🖐️ Pan Mode")
            self.labellingPressed()
            
    def adjust_brightness(self, delta):
        new_val = round(self.brightness_var.get() + delta, 1)
        self.brightness_var.set(new_val)
        self.update_image()

    def adjust_contrast(self, delta):
        new_val = round(self.contrast_var.get() + delta, 1)
        self.contrast_var.set(new_val)
        self.update_image()
        
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

    # ----------------- FAST decoders -----------------
    def OpenCargoImage(self, name):
        # Vectorized reader based on your original format logic.
        with open(name, 'rb') as f:
            f.read(8)   # d1
            f.read(4)   # d2
            ign = struct.unpack('<B', f.read(1))[0]
            f.read(3)   # d2b
            bpp = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<II', f.read(8))
            height, width = size[0], size[1]
            size2 = struct.unpack('<II', f.read(8))
            format1, flag = size2[0], size2[1]
            if ign == 24:
                # Y offset (unused here)
                _ = struct.unpack('<I', f.read(4))[0]
            f.read(8)  # d7

            if format1 > 2:
                # Interleaved hi/low words
                count = width * height * 2  # two planes interleaved
                data = np.frombuffer(f.read(count * 2), dtype='<u2', count=count)
                # even -> low, odd -> high
                high = data[1::2].reshape((width, height)).T
                low  = data[0::2].reshape((width, height)).T
            else:
                count = width * height
                data = np.frombuffer(f.read(count * 2), dtype='<u2', count=count)
                high = data.reshape((width, height)).T
                low = 0

        return high, low

    def OpenIMGimage(self, name):
        # Vectorized .img reader (your original logic without Python loops)
        with open(name, 'rb') as f:
            h1 = struct.unpack('<h', f.read(2))[0]
            s2  = struct.unpack('<h', f.read(2))[0]
            _ = struct.unpack('<h', f.read(2))[0]   # h3 skip?
            height3 = struct.unpack('<h', f.read(2))[0]
            width = struct.unpack('<h', f.read(2))[0]
            flag = struct.unpack('<h', f.read(2))[0]
            yPos = struct.unpack('<h', f.read(2))[0]
            flag2 = struct.unpack('<h', f.read(2))[0]

            f.read(2*25)  # skip 25 x 2 bytes

            f.read(s2)    # skip s2 bytes

            height = int(height3 / 3)

            data = np.frombuffer(f.read(width * height3 * 2), dtype='<u2', count=width*height3)
            data = data.reshape((width, height3))

            high = data[:, :height].T
            low  = data[:, height:2*height].T
            Zimage = data[:, 2*height:3*height].T

            # Flip as original code
            high = np.flipud(high)
            low  = np.flipud(low)
            Zimage = np.flipud(Zimage)

        return high, low

    # Unified, cached loader returning 8-bit RGB PIL Image
    def load_image(self, path):
        cached = self.cache.get(path)
        if cached is not None:
            return cached

        ext = os.path.splitext(path)[1].lower()

        if ext == '.cargoimage':
            high, _ = self.OpenCargoImage(path)
            p1, p99 = np.percentile(high, (1, 99))
            if p99 - p1 < 10:
                p1, p99 = float(high.min()), float(high.max())
            img8 = np.clip((high - p1) * 255.0 / max((p99 - p1), 1), 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img8, mode='L').convert('RGB')
        elif ext == '.img':
            high, _ = self.OpenIMGimage(path)
            p1, p99 = np.percentile(high, (1, 99))
            if p99 == p1:
                p1, p99 = float(high.min()), float(high.max())
            img8 = np.clip((high - p1) * 255.0 / max((p99 - p1), 1), 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img8, mode='L').convert('RGB')
        else:
            img_cv = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img_cv is None:
                raise ValueError("Failed to load image.")
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

        self.cache.put(path, pil_img)
        return pil_img

    def prefetch_neighbors(self):
        # Preload next/previous images in the background to make navigation smooth
        if not self.ImagePath:
            return
        n = len(self.ImagePath)
        idxs = [ (self.CurrentIndex + 1) % n, (self.CurrentIndex - 1) % n ]
        def worker(paths):
            for p in paths:
                try:
                    if self.cache.get(p) is None:
                        _ = self.load_image(p)
                except Exception:
                    pass
        threading.Thread(target=worker, args=( [self.ImagePath[i] for i in idxs], ), daemon=True).start()

    # ----------------- Display -----------------
    def showImagePaths(self):
        path = self.ImagePath[self.CurrentIndex]
        self.NumberShowing.delete(0, tk.END)
        self.NumberShowing.insert(0, f"{self.CurrentIndex + 1}/{len(self.ImagePath)}")

        self.InsidePath.delete(0, tk.END)
        self.InsidePath.insert(0, path)

        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

            # Fast, cached unified loader (returns 8-bit RGB PIL)
            pil_img = self.load_image(path)
            self.orig_img = pil_img
            orig_width, orig_height = pil_img.size

            # choose initial zoom scale to fit a reasonable preview
            max_w, max_h = 1525, 600
            if orig_width > max_w or orig_height > max_h:
                self.zoom_scale = min(max_w / orig_width, max_h / orig_height)
            else:
                self.zoom_scale = 1.0

            self.fit_zoom_scale = self.zoom_scale  # store the minimum allowed zoom

            disp_w = int(orig_width * self.zoom_scale)
            disp_h = int(orig_height * self.zoom_scale)
            disp_img = pil_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            self.img = disp_img
            self.img_tk = ImageTk.PhotoImage(disp_img)

            # place image at 0,0 and set scrollregion
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
            self.mask_data = None
            self.mask_visible = False
            self.tk_mask_overlay = None
            self.mask_overlay_id = None

            # load any existing json annotations
            label_path = os.path.splitext(path)[0] + "_label.json"
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    data = json.load(f)
                    for shape in data.get("shapes", []):
                        if shape.get("shape_type") == "polygon":
                            points = shape.get("points", [])
                            # store as floats in original image coords
                            pts_float = [(float(p[0]), float(p[1])) for p in points]
                            self.temp_shapes.append(pts_float)

            self.redraw_canvas()
            # Kick off neighbor prefetch in background (non-blocking)
            self.prefetch_neighbors()

        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image:\n{e}")

    def show_pixel(self, event):
        if self.orig_img is None:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        img_x = int((canvas_x - self.img_x) / self.zoom_scale)
        img_y = int((canvas_y - self.img_y) / self.zoom_scale)

        orig_w, orig_h = self.orig_img.size
        if 0 <= img_x < orig_w and 0 <= img_y < orig_h:
            pixel = self.orig_img.getpixel((img_x, img_y))
            self.coord_label.config(text=f"({img_x},{img_y}) Value={pixel}")
        else:
            self.coord_label.config(text="(0,0) Value=(0, 0, 0)")

    def confirm_save_before_switch(self, direction):
        if self.shapes_modified:
            result = messagebox.askquestion("Save Polygon?", "Do you want to save the polygon drawn?", icon='warning')
            if result == 'yes':
                self.savePressed(force=True)
            else:
                self.new_shapes.clear()
                self.shapes_modified = False

        if direction == "next":
            self.CurrentIndex += 1
            if self.CurrentIndex >= len(self.ImagePath):
                self.CurrentIndex = 0
        elif direction == "prev":
            self.CurrentIndex -= 1
            if self.CurrentIndex < 0:
                self.CurrentIndex = len(self.ImagePath) - 1
        self.showImagePaths()

    def nextPressed(self):
        if self.ImagePath:
            self.confirm_save_before_switch("next")

    def previousPressed(self):
        if self.ImagePath: 
            self.confirm_save_before_switch("prev")

    def undoPressed(self, event=None):
        if self.points:
            self.points.pop()
            self.redraw_canvas()
        else:
            messagebox.showinfo("Undo", "No  points to undo.")
            return
        
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
        self.hover_highlight_id = None  # ID of the temporary highlight

        def on_motion(event):
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            overlapping = self.canvas.find_overlapping(cx, cy, cx, cy)

            # Remove previous highlight
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
                        for (x, y) in shape
                    ]
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
                    self.canvas.delete(item)
                    del self.polygon_id[index]
                    del self.temp_shapes[index]
                    self.shapes_modified = True
                    self.update_msk_file()
                    self.redraw_canvas()
                    break
            # Clean up
            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<Button-1>")
            if self.hover_highlight_id:
                self.canvas.delete(self.hover_highlight_id)
                self.hover_highlight_id = None

        self.canvas.bind("<Motion>", on_motion)
        self.canvas.bind("<Button-1>", on_click)

    def update_msk_file(self):
        if not self.ImagePath:
            return
        image_path = self.ImagePath[self.CurrentIndex]
        msk_path = os.path.splitext(image_path)[0] + "_label.msk"
        orig_w, orig_h = self.orig_img.size
        mask = np.zeros((orig_w, orig_h), dtype=np.uint8)
        for shape in self.temp_shapes:
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
        self.enable_polygon_deletion()
        
    def render_overlays(self):
        self.canvas.delete("polygon")
        self.canvas.delete("temp_point")
        self.canvas.delete("temp_line")

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

        # Draw current points and lines
        for i, point in enumerate(self.points):
            sx = int(round(point[0] * self.zoom_scale)) + self.img_x
            sy = int(round(point[1] * self.zoom_scale)) + self.img_y
            self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="red", tags="temp_point")

            if i > 0:
                prev = self.points[i-1]
                px = int(round(prev[0] * self.zoom_scale)) + self.img_x
                py = int(round(prev[1] * self.zoom_scale)) + self.img_y
                self.canvas.create_line(px, py, sx, sy, fill="red", width=2, tags="temp_line")

        # Mask overlay
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

    def save_msk_file(self, image_path, shapes):
        # Save binary .msk and optional png
        orig_w, orig_h = self.orig_img.size
        mask = np.zeros((orig_w, orig_h), dtype=np.uint8)
        for shape in shapes:
            pts = np.array([[int(round(y)), int(round(x))] for x, y in shape], dtype=np.int32)
            if pts.size == 0:
                continue
            cv2.fillPoly(mask, [pts], 255)

        msk_path = os.path.splitext(image_path)[0] + "_label.msk"
        if os.path.exists(msk_path):
            os.remove(msk_path)
        with open(msk_path, "wb") as f:
            f.write(struct.pack('II', orig_h, orig_w))
            f.write(mask.tobytes())

        if self.show_mask_var.get():
            try:
                png_path = os.path.splitext(image_path)[0] + "_mask.png"
                img = Image.fromarray(mask.T)  # L
                img.save(png_path)
                print("PNG saved:", png_path)
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
        
    def zoomOutPressed(self):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        center_x = canvas_w // 2
        center_y = canvas_h // 2
        self.zoom_at(1.0 / 1.2, center_x, center_y)

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

    # ----------------- Mask overlay / show/hide -----------------
    def show_msk_file(self, event=None):
        if not self.ImagePath:
            messagebox.showerror("Missing", "No image loaded")
            return
        image_path = self.ImagePath[self.CurrentIndex]
        msk_path = os.path.splitext(image_path)[0] + "_label.msk"
        if not os.path.exists(msk_path):
            messagebox.showerror("Missing", "No .msk file found for current image")
            return

        if getattr(self, "mask_visible", False):
            if hasattr(self, "mask_overlay_id") and self.mask_overlay_id is not None:
                self.canvas.delete(self.mask_overlay_id)
            self.mask_visible = False
            return

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
        if hasattr(self, "mask_overlay_id") and self.mask_overlay_id is not None:
            self.canvas.delete(self.mask_overlay_id)
        self.mask_overlay_id = self.canvas.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.tk_mask_overlay)

    def close_msk_file(self, event=None):
        if hasattr(self, "mask_overlay_id") and self.mask_overlay_id is not None:
            self.canvas.delete(self.mask_overlay_id)
            self.mask_overlay_id = None
            self.mask_visible = False

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

    # ----------------- Labeling -----------------
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
            if len(self.points) > 2:
                self.temp_shapes.append([(float(x), float(y)) for x, y in self.points])
                self.new_shapes.append(list(self.points))
                self.shapes_modified = True
                self.redraw_canvas()
            else:
                messagebox.showinfo("Polygon Error", "Need at least 3 points to form a polygon.")
                return

            # Clear temp visuals
            for line_id in self.temp_line_ids:
                self.canvas.delete(line_id)
            self.temp_line_ids.clear()

            for point_id in self.temp_point_ids:
                self.canvas.delete(point_id)
            self.temp_point_ids.clear()

            self.points.clear()

        self.canvas.bind("<Button-1>", on_left_click)
        self.canvas.bind("<Button-3>", on_right_click)
        self.canvas.focus_set()

    def update_image(self,value=None):     
        if self.orig_img is None:
            return

        brightness = self.brightness_var.get()
        contrast = self.contrast_var.get()

        img_np = np.array(self.orig_img).astype(np.float32)
        img_np = img_np * contrast + (brightness - 1.0) * 255
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)

        adjusted_img = Image.fromarray(img_np)

        disp_w = int(adjusted_img.size[0] * self.zoom_scale)
        disp_h = int(adjusted_img.size[1] * self.zoom_scale)
        disp_img = adjusted_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

        self.img = disp_img
        self.img_tk = ImageTk.PhotoImage(disp_img)

        self.canvas.delete("base_image")
        self.canvas.create_image(self.img_x, self.img_y, image=self.img_tk, anchor=tk.NW, tags="base_image")
        self.render_overlays()
        
    def reset_brightness_contrast(self):
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.update_image()

    # ----------------- Save -----------------
    def savePressed(self, force=False):
        if not self.shapes_modified && not force:
            return

        image_path = self.ImagePath[self.CurrentIndex]
        base_name, extension = os.path.splitext(image_path)
        selected_format = self.formatSelector.get()

        if selected_format in ("json", "both"):
            save_path = base_name + "_label.json"
            orig_w, orig_h = self.orig_img.size
            data = {
                "version": "1.0.0",
                "shapes": [],
                "imagePath": os.path.basename(image_path),
                "imageData": None,
                "imageHeight": orig_h,
                "imageWidth": orig_w
            }
            for shape_points in self.temp_shapes:
                converted_points = []
                for point in shape_points:
                    x = int(round(point[0]))
                    y = int(round(point[1]))
                    converted_points.append([x, y])
                shape = {
                    "label": "container",
                    "points": converted_points,
                    "group_id": None,
                    "description": "",
                    "shape_type": "polygon",
                    "mask": None
                }
                data["shapes"].append(shape)

            with open(save_path, "w") as file:
                json.dump(data, file, indent=4)

        if selected_format in ("msk", "both"):
            self.save_msk_file(image_path, self.temp_shapes)

        self.new_shapes.clear()
        self.shapes_modified = False

# run
if __name__ == "__main__":
    Load_file()
