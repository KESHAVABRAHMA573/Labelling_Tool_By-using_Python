# Labelling_Tool_By-using_Python


# 🖼️ File Loader and Polygon Labeling Tool

This Python application provides a GUI for loading images from a `.txt` file, viewing them, and interactively labeling regions using polygon shapes. It supports undo/redo functionality and saves annotations in JSON format.

## 📦 Features

- Load image paths from a `.txt` file
- Display images with zoomed window
- Show pixel RGB values on mouse hover
- Navigate through image list (Next/Previous)
- Start polygon-based labeling with mouse clicks
- Undo/Redo polygon shapes
- Save labeled polygons to a JSON file
- Clear/reset interface

## 🛠️ Requirements

- Python 3.x
- [Pillow](https://pypi.org/project/Pillow/) (`pip install pillow`)

## 🚀 How to Run

1. Ensure your `.txt` file contains valid paths to `.jpg` or `.png` images (one per line).
2. Run the script:
   ```bash
   python your_script_name.py
