# imports
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QWidget
from input_page import InputPage

# main window class
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # set all properties
        self.setObjectName("main")
        self.setStyleSheet("QMainWindow#main { background-color: #CDD3D5; }")

        self.setWindowTitle("Data acquisition pipeline")
        self.setMinimumSize(1280,720)

        self.setCentralWidget(InputPage(self))

# main
if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())