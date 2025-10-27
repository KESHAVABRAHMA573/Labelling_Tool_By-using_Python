
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk, ImageDraw
import json
import struct
import numpy as np
import cv2
class Load_file:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Loader")
        self.root.state('zoomed')
        self.ImagePath = []
        self.CurrentIndex = 0
        self.labelling=0
        self.points=[]
        self.polygon_id=[]
        self.temp_shapes = []
        self.redo_stack=[]
        self.new_shapes=[]
        self.shapes_modified = False
        self.temp_line_ids = []
        self.temp_point_ids = []
        self.orig_img=None
        self.zoom_scale=1.0
        self.offset_x=0.0
        self.offset_y=0.0
        self.min_zoom=0.1
        self.max_zoom=8.0

        # Create top and bottom frames
        self.top_frame = tk.Frame(self.root, bg="white")
        self.top_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.root, bg="lightgray")
        self.bottom_frame.pack(fill="x",pady=(0,40))
        
        self.canvas = tk.Canvas(self.top_frame, bg="white")
        self.canvas.pack(expand=True)


        self.enable_click_to_zoom()
        # Controls in bottom frame
        self.Listfile = tk.Label(self.bottom_frame, text="List File:")
        self.Listfile.grid(row=0, column=0, padx=10, pady=10)

        self.Load1 = tk.Entry(self.bottom_frame, width=50)
        self.Load1.grid(row=0, column=1, padx=10, pady=10)

        self.Browse = tk.Button(self.bottom_frame, text="Browse", command=self.browsePressed)
        self.Browse.grid(row=0, column=2, padx=10, pady=10)

        self.Load = tk.Button(self.bottom_frame, text="Load", command=self.loadPressed)
        self.Load.grid(row=1, column=1, padx=10, pady=10)

        self.Clear = tk.Button(self.bottom_frame, text="Clear", command=self.clearPressed)
        self.Clear.grid(row=1, column=2, padx=10, pady=10)

        self.NumberShowing = tk.Entry(self.bottom_frame, width=5)
        self.NumberShowing.grid(row=2, column=0, padx=10, pady=10)

        self.InsidePath = tk.Entry(self.bottom_frame, width=50)
        self.InsidePath.grid(row=2, column=1, padx=10, pady=10)

        self.Previous = tk.Button(self.bottom_frame, text="Previous", command=self.previousPressed)
        self.Previous.grid(row=2, column=2, padx=10, pady=10)

        self.Next = tk.Button(self.bottom_frame, text="Next", command=self.nextPressed)
        self.Next.grid(row=2, column=3, padx=10, pady=10)

        self.save=tk.Button(self.bottom_frame ,text="Save",command=self.savePressed)
        self.save.grid(row=0,column=11,padx=10,pady=10)

        # Coordinate label
        self.coord_label = tk.Label(self.bottom_frame, text="X: 0, Y: 0",width=50 ,height=2,font=("Bold",10))
        self.coord_label.grid(row=0, column=5,padx=10, pady=10)


        self.Labeling=tk.Button(self.bottom_frame,text="Start labelling",command=self.labellingPressed)
        self.Labeling.grid(row=0,column=9,padx=10,pady=10)

        self.Undo=tk.Button(self.bottom_frame,text="Undo",command= self.undoPressed)
        self.Undo.grid(row=2,column=9,padx=10,pady=10)

        self.Delete=tk.Button(self.bottom_frame,text="Delete",command=self.deletePressed)
        self.Delete.grid(row=2,column=11,padx=10,pady=10)

        self.formatSelector=tk.StringVar(value="json")

        self.json=tk.Radiobutton(self.bottom_frame,text="  Json   ",variable=self.formatSelector, value="json")
        self.json.grid(row=0,column=14,padx=10,pady=10)

        self.msk=tk.Radiobutton(self.bottom_frame,text="   MSK    ",variable=self.formatSelector,value="msk")
        self.msk.grid(row=1,column=14,padx=10,pady=10)

        self.both=tk.Radiobutton(self.bottom_frame,text="Json & MSK",variable=self.formatSelector, value="both")
        self.both.grid(row=2,column=14,padx=10,pady=10)

        self.ShowMaskFile=tk.Button(self.bottom_frame, text="Show_MSk_File")
        self.ShowMaskFile.grid(row=1,column=15,padx=10,pady=10)

        self.ShowMaskFile.bind("<ButtonPress-1>", self.show_msk_file)
        self.ShowMaskFile.bind("<ButtonRelease-1>", self.close_msk_file)

        self.show_mask_var = tk.IntVar(value=False)
        self.mask_checkbox = tk.Checkbutton(self.bottom_frame,text="PNG Also?",variable=self.show_mask_var)
        self.mask_checkbox.grid(row=1, column=11, padx=10, pady=10)

        self.zoomin=tk.Button(self.bottom_frame,text="Zoom_in",command=self.zoomInPressed)
        self.zoomin.grid(row=2,column=15,padx=10,pady=10)

        self.zoomout=tk.Button(self.bottom_frame,text="Zoom_out",command=self.zoomOutPressed)
        self.zoomout.grid(row=2,column=16,padx=10,pady=10)

        
        self.root.mainloop()

    def browsePressed(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")], title="Select a .txt file")
        if file_path:
            self.Load1.delete(0, tk.END)
            self.Load1.insert(0, file_path)

    def clearPressed(self):
        self.Load1.delete(0, tk.END)
        self.NumberShowing.delete(0, tk.END)
        self.InsidePath.delete(0, tk.END)
        self.canvas.delete("all")
        self.coord_label.config(text="X: 0, Y: 0")
        

    def loadPressed(self):
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
                    if stripped.lower().endswith(('.jpg','.png')) and os.path.exists(stripped):
                        self.ImagePath.append(stripped)
            if self.ImagePath:
                self.CurrentIndex = 0
                self.showImagePaths()
            else:
                messagebox.showerror("Empty File", "No valid image paths found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def showImagePaths(self):
        path = self.ImagePath[self.CurrentIndex]
        self.NumberShowing.delete(0, tk.END)
        self.NumberShowing.insert(0, f"{self.CurrentIndex + 1}/{len(self.ImagePath)}")

        self.InsidePath.delete(0, tk.END)
        self.InsidePath.insert(0, path)

        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            with Image.open(path) as img_check:
                img_check.verify()

            img = Image.open(path).convert("RGB")
            self.orig_img = img
            orig_width, orig_height = img.size
            max_w, max_h = 1525, 600

            if orig_width > max_w or orig_height > max_h:
                initial_zoom = min(max_w / orig_width, max_h / orig_height)
            else:
                initial_zoom = 1.0

            self.zoom_scale = initial_zoom
            self.offset_x = 0
            self.offset_y = 0

            disp_w = max(1, int(orig_width * self.zoom_scale))
            disp_h = max(1, int(orig_height * self.zoom_scale))
            disp_img = img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

            self.img = disp_img.convert("RGB")
            self.img_tk = ImageTk.PhotoImage(self.img)

            self.canvas.delete("all")
            self.canvas.config(width=self.img_tk.width(), height=self.img_tk.height())
            img_x = int(-self.offset_x * self.zoom_scale)
            img_y = int(-self.offset_y * self.zoom_scale)
            self.canvas.create_image(img_x, img_y, image=self.img_tk, anchor=tk.NW)
            self.canvas.bind("<Motion>", self.show_pixel)

            self.points.clear()
            self.temp_line_ids.clear()
            self.temp_point_ids.clear()
            self.temp_shapes.clear()
            self.polygon_id.clear()

            label_path = os.path.splitext(path)[0] + "_label.json"
            if os.path.exists(label_path):
                try:
                    with open(label_path, "r") as f:
                        data = json.load(f)
                        for shape in data.get("shapes", []):
                            if shape.get("shape_type") == "polygon":
                                points = shape.get("points", [])
                                self.temp_shapes.append(points)
                except Exception as e:
                    print(f"Error loading saved polygons: {e}")

            self.redraw_canvas()

        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image:\n{e}")


    def show_pixel(self, event):
        if self.orig_img is None:
            return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        img_x = int(canvas_x / self.zoom_scale)
        img_y = int(canvas_y / self.zoom_scale)


        orig_w, orig_h = self.orig_img.size
        if 0 <= img_x < orig_w and 0 <= img_y < orig_h:
            pixel = self.orig_img.getpixel((img_x, img_y))
            self.coord_label.config(text=f"({img_x},{img_y}) Value={pixel}")
        else:
            self.coord_label.config(text=f"(out of bounds) X:{img_x},Y:{img_y}")
    def nextPressed(self):
        if self.ImagePath:
            self.CurrentIndex +=1
            if self.CurrentIndex >= len(self.ImagePath):
                self.CurrentIndex = 0

            self.showImagePaths()

    def previousPressed(self):
        if self.ImagePath:
            self.CurrentIndex -= 1
            if self.CurrentIndex < 0:
                self.CurrentIndex=len(self.ImagePath)-1
            self.showImagePaths()

    def undoPressed(self):
        if self.points:
            self.points.pop()
            self.redraw_canvas()

        else:
            messagebox.showinfo("Undo", "No poiints are there to undo these")
    def enable_polygon_deletion(self):
        def on_click(event):
            clicked_items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in reversed(clicked_items):
                if item in self.polygon_id:
                    index = self.polygon_id.index(item)
                    self.canvas.delete(item)
                    del self.polygon_id[index]
                    del self.temp_shapes[index]
                    self.shapes_modified = True
                    self.update_msk_file()
                    self.redraw_canvas()
                    break  
            self.canvas.unbind("<Button-1>")  

        self.canvas.bind("<Button-1>", on_click)

    def update_msk_file(self):
        image_path = self.ImagePath[self.CurrentIndex]
        msk_path = os.path.splitext(image_path)[0] + "_label.msk"
        png_path = os.path.splitext(image_path)[0] + "_mask.png"
        mask = np.zeros((self.img.height, self.img.width), dtype=np.uint8)
        for shape in self.temp_shapes:  
            pts = np.array(shape, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

        with open(msk_path, "wb") as f:
            f.write(struct.pack('II', self.img.height, self.img.width))
            f.write(mask.tobytes())
        if self.show_mask_var.get():
            try:
                mask_uint8 = (mask > 0).astype(np.uint8) * 255  # Convert to 0/255
                img = Image.fromarray(mask_uint8, mode="L")     # Grayscale image
                png_path = os.path.splitext(image_path)[0] + "_mask.png"
                img.save(png_path)
                
            except Exception as e:
                print("Failed to save PNG:", e)

    def deletePressed(self):
        self.enable_polygon_deletion()
        self.update_msk_file()

    def redraw_canvas(self):
        if self.orig_img is None:
            return

        orig_w, orig_h = self.orig_img.size
        disp_w = int(orig_w * self.zoom_scale)
        disp_h = int(orig_h * self.zoom_scale)

    # Choose resampling method based on zoom direction
        if self.zoom_scale >= 1.0:
            resample_method = Image.Resampling.NEAREST  # Preserve sharpness when zooming in
        else:
            resample_method = Image.Resampling.LANCZOS  # Smooth when zooming out

        disp_img = self.orig_img.resize((disp_w, disp_h), resample_method)
        self.img = disp_img
        self.img_tk = ImageTk.PhotoImage(self.img)

        self.canvas.config(scrollregion=(0, 0, disp_w, disp_h))
        self.canvas.config(width=disp_w, height=disp_h)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)

        self.polygon_id.clear()
        for shape in self.temp_shapes:
            screen_pts = [(int(x * self.zoom_scale), int(y * self.zoom_scale)) for (x, y) in shape]
            flat = [coord for pt in screen_pts for coord in pt]
            polygon_id = self.canvas.create_polygon(flat, outline="red", fill='', width=2)
            self.polygon_id.append(polygon_id)

        for i, point in enumerate(self.points):
            sx = int(point[0] * self.zoom_scale)
            sy = int(point[1] * self.zoom_scale)
            self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="red")
            if i > 0:
                prev = self.points[i-1]
                px = int(prev[0] * self.zoom_scale)
                py = int(prev[1] * self.zoom_scale)
                self.canvas.create_line(px, py, sx, sy, fill="red", width=2)


    def save_annotated_image(self, image_path, shapes):
        annotated_img = self.img.copy()
        draw = ImageDraw.Draw(annotated_img)
        for shape in shapes:
            draw.polygon(shape, outline="red")
        annotated_path = os.path.splitext(image_path)[0] + "_labelled.png"
        annotated_img.save(annotated_path)

    def save_msk_file(self, image_path, shapes):
        orig_w, orig_h = self.orig_img.size
        mask = np.zeros((self.img.height, self.img.width),dtype=np.uint8)

        for shape in shapes:
            pts = np.array(shape, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

        msk_path=os.path.splitext(image_path)[0]+"_label.msk"
        if os.path.exists(msk_path):
            os.remove(msk_path)

        with open(msk_path,"wb") as f:
            f.write(struct.pack('II',self.img.height, self.img.width))
            f.write(mask.tobytes())
        if self.show_mask_var.get():
            try:
                mask_uint8 = (mask > 0).astype(np.uint8) * 255
                img = Image.fromarray(mask_uint8, mode="L")
                png_path = os.path.splitext(image_path)[0] + "_mask.png"
                img.save(png_path)
                print("PNG saved:", png_path)
            except Exception as e:
                print("Failed to save PNG:", e)
    def draw_mask_overlay(self):
        if self.mask_data is None or self.orig_img is None:
            return
        
        orig_w, orig_h = self.orig_img.size
        scaled_w = int(orig_w * self.zoom_scale)
        scaled_h = int(orig_h * self.zoom_scale)
        mask_img = Image.fromarray((self.mask_data * 255).astype(np.uint8)).convert("L")
        mask_img = mask_img.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)

        self.mask_tk = ImageTk.PhotoImage(mask_img)
        self.mask_overlay_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_mask_overlay)


     
    def savePressed(self,force=False):
        if not self.shapes_modified and not force:
            return  

        image_path = self.ImagePath[self.CurrentIndex]
        base_name,extension = os.path.splitext(image_path)
        selected_format = self.formatSelector.get()

        if selected_format in ("json","both"):
            save_path = base_name + "_label.json"
            orig_weight,orig_height=self.orig_img.size
            data = {
                "version": "1.0.0",
                "shapes": [],
                "imagePath": os.path.basename(image_path),
                "imageData": None,
                "imageHeight": orig_height,
                "imageWidth": orig_weight
            }
            for shape_points in self.temp_shapes:
                converted_points = []
                for point in shape_points:
                    x = int(point[0])
                    y = int(point[1])
                    converted_points.append([x, y])
                shape = {}
                shape["label"] = "container"
                shape["points"] = converted_points
                shape["group_id"] = None
                shape["description"] = ""
                shape["shape_type"] = "polygon"
                shape["mask"] = None
                data["shapes"].append(shape)


            with open(save_path, "w") as file:
                json.dump(data, file, indent=4)
        if selected_format in ("msk","both"):
            self.save_msk_file(image_path,self.temp_shapes)
            
        self.new_shapes.clear()
        self.shapes_modified = False

    def open_msk_file(self, msk_path):
        try:
            mask_img = Image.open(msk_path).convert("L")
            mask_img.show()

            return mask_img
        except Exception as e:
            print(f"Failed to open .msk file: {e}")
            
    def enable_click_to_zoom(self):
        def zoom_in(event):
            self.zoom_at(1.5, event.x, event.y)
        def zoom_out(event):
            self.zoom_at(1.0 / 1.5, event.x, event.y)

        self.canvas.bind("<Shift-Button-1>", zoom_in)
        self.canvas.bind("<Shift-Button-3>", zoom_out)
        
    def view_msk_file(self, msk_path):

        if not os.path.exists(msk_path):
            messagebox.showerror("Missing", f"File not found:\n{msk_path}")
            return

        with open(msk_path, "rb") as f:
            header = f.read(8)
            h, w = struct.unpack('II', header)
            data = f.read()
            mask = np.frombuffer(data, dtype=np.uint8).reshape((h, w))

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
        #new_zoom = old_zoom * factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, old_zoom * factor))
        
        img_x = screen_x / old_zoom + self.offset_x
        img_y = screen_y / old_zoom + self.offset_y
        
        self.zoom_scale = new_zoom
        self.offset_x = img_x - screen_x / new_zoom
        self.offset_y = img_y - screen_y / new_zoom
        
        max_offset_x = max(0, self.orig_img.size[0] - self.canvas.winfo_width() / self.zoom_scale)
        max_offset_y = max(0, self.orig_img.size[1] - self.canvas.winfo_height() / self.zoom_scale)

        self.offset_x = max(0, min(self.offset_x, max_offset_x))
        self.offset_y = max(0, min(self.offset_y, max_offset_y))

        self.redraw_canvas()
        
    '''def _on_mouse_wheel(self, event):
        
        if hasattr(event, "delta"):
            delta = event.delta
        else:

            if event.num == 4:
                delta = 120
            else:
                delta = -120
        if delta > 0:
            self.zoom_at(1.2, event.x, event.y)
        else:
            self.zoom_at(1.0 / 1.2, event.x, event.y)'''
    

    def show_msk_file(self, event=None):
        image_path = self.ImagePath[self.CurrentIndex]
        msk_path = os.path.splitext(image_path)[0] + "_label.msk"
        if not os.path.exists(msk_path):
            messagebox.showerror("Missing", "No .msk file found for current image")
            return

        with open(msk_path, "rb") as f:
            header = f.read(8)
            h, w = struct.unpack('II', header)
            data = f.read()
            mask = np.frombuffer(data, dtype=np.uint8).reshape((h, w))
        self.mask_data=mask
        
        scaled_w = int(w * self.zoom_scale)
        scaled_h = int(h * self.zoom_scale)
        visible_mask = np.where(mask > 0, 255, 0).astype(np.uint8)
        
        mask_img = Image.fromarray(visible_mask).convert("L")
        mask_img = mask_img.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)

        self.tk_mask_overlay = ImageTk.PhotoImage(mask_img)
        self.mask_overlay_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_mask_overlay)

    def close_msk_file(self, event=None):
        if hasattr(self, "mask_overlay_id"):
            self.canvas.delete(self.mask_overlay_id)
            del self.mask_overlay_id
    def show_msk_pressed(self):
        if self.orig_img is None or self.mask_data is None:
            return
        self.zoom_scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.redraw_canvas()

        self.draw_mask_overlay()

    def labellingPressed(self):
        
        def on_left_click(event):

            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            
            img_x = canvas_x / self.zoom_scale
            img_y = canvas_y / self.zoom_scale
            
            orig_w, orig_h = self.orig_img.size
            img_x = min(max(img_x, 0), orig_w - 1)
            img_y = min(max(img_y, 0), orig_h - 1)


            self.points.append((img_x, img_y))

            sx = int(img_x * self.zoom_scale)
            sy = int(img_y * self.zoom_scale)
            point_id = self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="red")
            self.temp_point_ids.append(point_id)

            if len(self.points) > 1:
                prev = self.points[-2]
                px = int(prev[0] * self.zoom_scale)
                py = int(prev[1] *  self.zoom_scale)
                line_id = self.canvas.create_line(px, py, sx, sy, fill="red", width=2)
                self.temp_line_ids.append(line_id)

        def on_right_click(event):

            self.shapes_modified = True
            if len(self.points) > 2:
                polygon_id = self.canvas.create_polygon(
                    [coord for p in [(int(x * self.zoom_scale), int(y  * self.zoom_scale)) for x, y in self.points] for coord in p],
                    outline="red", fill='', width=2)
                self.polygon_id.append(polygon_id)
                self.temp_shapes.append([(float(x), float(y)) for x, y in self.points])
                self.new_shapes.append(list(self.points))

            for line_id in self.temp_line_ids:
                self.canvas.delete(line_id)
            self.temp_line_ids.clear()
            for point_id in self.temp_point_ids:
                self.canvas.delete(point_id)
            self.temp_point_ids.clear()
            self.points.clear()
                
        self.canvas.bind("<Button-1>" ,on_left_click)
        self.canvas.bind("<Button-3>" ,on_right_click)
        self.root.bind("<BackSpace>", lambda event :self.undoPressed())
        
        '''self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)        # Windows
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)         # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)''' 
        
        self.canvas.focus_set()

Load_file()
