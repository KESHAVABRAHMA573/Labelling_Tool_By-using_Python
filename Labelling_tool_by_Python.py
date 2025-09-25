import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk
import json

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


        # Create top and bottom frames
        self.top_frame = tk.Frame(self.root, bg="white")
        self.top_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.root, bg="lightgray")
        self.bottom_frame.pack(fill="x")

        # Canvas for image display
        self.canvas = tk.Canvas(self.top_frame, bg="white")
        self.canvas.pack(expand=True)

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

        self.Redo=tk.Button(self.bottom_frame,text="Redo",command=self.redoPressed)
        self.Redo.grid(row=2,column=11,padx=10,pady=10)


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
                    if stripped.lower().endswith(('.jpg', '.png')) and os.path.exists(stripped):
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
            img = Image.open(path)
            img = img.resize((500, 500))
            self.img_tk = ImageTk.PhotoImage(img)

            self.img=img

            self.canvas.delete("all")
            self.canvas.config(width=self.img_tk.width(), height=self.img_tk.height())
            self.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)
            self.canvas.bind("<Motion>", self.show_pixel)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image:\n{e}")

    def show_pixel(self, event):
        x, y = event.x,event.y
        if 0 <= x < self.img.width and 0<=y < self.img.height:
            pixel=self.img.getpixel((x,y))
            self.coord_label.config(text=f"Pixel at ({x},{y}) It's RGB Value:{(pixel)}")# Have to ask'''

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
        if self.temp_shapes:
            last_shape = self.temp_shapes.pop()
            self.redo_stack.append(last_shape)
            self.redraw_canvas()
        else:
            messagebox.showinfo("Undo", "No polygon to undo.")


    def redoPressed(self):
        if self.redo_stack:
            shape = self.redo_stack.pop()
            self.temp_shapes.append(shape)
            self.redraw_canvas()
        else:
            messagebox.showinfo("Redo", "No polygon to redo.")

    def savePressed(self):
        if self.temp_shapes:
            for shape_points in self.temp_shapes:
                self.save_polygon(shape_points)
                self.temp_shapes.clear()
            #messagebox.showinfo("Saved", "Polygons saved successfully.")
        else:
            messagebox.showwarning("No Shapes", "No polygons to save.")
    def redraw_canvas(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)
        for shape in self.temp_shapes:
            self.canvas.create_polygon(shape, outline="red", fill='', width=2)

    def savePressed(self):
        image_path = self.ImagePath[self.CurrentIndex]
        base_name, extension = os.path.splitext(image_path)
        save_path = base_name + "_label.json"

        data = {
            "version": "1.0.0",
            "shapes": []
        }

    # Load existing shapes if file exists
        if os.path.exists(save_path):
            try:
                with open(save_path, "r") as file:
                    content = file.read().strip()
                    if content:
                        data = json.loads(content)
            except json.JSONDecodeError:
                print("Warning: JSON file is empty or corrupted. Starting fresh.")

    # Add all collected polygons
        for shape_points in self.temp_shapes:
            converted_points = [[int(x), int(y)] for x, y in shape_points]
            shape = {
                "label": "container",
                "points": converted_points,
                "group_id": None,
                "description": "",
                "shape_type": "polygon",
                "mask": None
            }
            data["shapes"].append(shape)

    # Add image metadata
        data["imagePath"] = os.path.basename(image_path)
        data["imageData"] = None
        data["imageHeight"] = self.img.height
        data["imageWidth"] = self.img.width

    # Save to file
        with open(save_path, "w") as file:
            json.dump(data, file, indent=4)

        self.temp_shapes.clear()
        messagebox.showinfo("Saved", "All polygons saved successfully.")

    def labellingPressed(self):
        def on_left_click(event):
            self.points.append((event.x,event.y))
            self.canvas.create_oval(event.x-2,event.y-2,event.x+2,event.y+2,fill="red")
            if len(self.points)>1:
                self.canvas.create_line(self.points[-2],self.points[-1],fill="red",width=2)

        def on_right_click(event):
            if len(self.points) > 2:
                self.canvas.create_polygon(self.points,outline="red",fill='',width=2)

                self.temp_shapes.append(list(self.points))
            self.redo_stack.clear()
            self.points.clear()
        
        
        self.canvas.bind("<Button-1>" ,on_left_click)
        self.canvas.bind("<Button-3>" ,on_right_click)

        



Load_file()
