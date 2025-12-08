import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class FileSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Selector")
        self.root.geometry("400x200")

        # ----- Main Button -----
        self.create_btn = ttk.Button(root, text="Create File", command=self.open_dropdown_menu)
        self.create_btn.pack(pady=50)

    # -----------------------------
    # DROPDOWN MENU WHEN BUTTON PRESSED
    # -----------------------------
    def open_dropdown_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Select File", command=self.select_file)
        menu.add_command(label="Select Folder", command=self.select_folder)

        # Popup menu at mouse pointer
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    # -----------------------------
    # FILE SELECTION WITH FILTERS
    # -----------------------------
    def select_file(self):
        file_types = [
            ("PNG Images", "*.png"),
            ("JPEG Images", "*.jpg"),
            ("JPEG Images", "*.jpeg"),
            ("All Files", "*.*")
        ]

        filepath = filedialog.askopenfilename(
            title="Select a File",
            filetypes=file_types
        )

        if filepath:
            messagebox.showinfo("File Selected", f"Selected File:\n{filepath}")

    # -----------------------------
    # FOLDER SELECTION
    # -----------------------------
    def select_folder(self):
        folderpath = filedialog.askdirectory(title="Select a Folder")

        if folderpath:
            messagebox.showinfo("Folder Selected", f"Selected Folder:\n{folderpath}")


# -----------------------------
# RUN APPLICATION
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    FileSelectorApp(root)
    root.mainloop()
