from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
from PySide6.QtGui import QAction
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VS Code-like Menu Demo")

        # ---- MENU BAR ----
        menubar = self.menuBar()

        # ---- FILE MENU ----
        file_menu = menubar.addMenu("File")

        # Level 1
        open_menu = QMenu("Open", self)
        file_menu.addMenu(open_menu)

        # Level 2
        open_file_action = QAction("Open File…", self)
        open_folder_action = QAction("Open Folder…", self)
        open_menu.addAction(open_file_action)
        open_menu.addAction(open_folder_action)

        # Level 2 → deeper submenu
        recent_menu = QMenu("Recent", self)
        open_menu.addMenu(recent_menu)

        # Level 3 items
        recent_menu.addAction(QAction("Project 1", self))
        recent_menu.addAction(QAction("Project 2", self))
        recent_menu.addAction(QAction("Browse Recent…", self))

        # Another File option
        save_action = QAction("Save As…", self)
        file_menu.addAction(save_action)

        # Separator like VS Code
        file_menu.addSeparator()

        # Quit
        quit_action = QAction("Exit", self)
        file_menu.addAction(quit_action)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
