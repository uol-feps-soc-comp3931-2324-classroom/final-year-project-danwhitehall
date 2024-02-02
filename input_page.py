# all imports
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction, QIcon
from file_info import fileInfo

# class for the input page
class InputPage(QWidget):
    def __init__(self, MainWindow):
        super().__init__()
        # set the main window
        self.MainWindow = MainWindow
        self.window_width = self.MainWindow.width()
        self.window_height = self.MainWindow.height()

        # create the layout
        # layout = QBoxLayout()
        # layout.setAlignment(Qt.AlignmentFlag.AlignVertical_Mask)

        # create the toolbar 
        toolbar = QToolBar()
        self.MainWindow.addToolBar(toolbar)

        # create open file button for toolbar
        open_file_button = QAction("Open File", self)
        open_file_button.setStatusTip("Open a file")
        open_file_button.triggered.connect(self.open_file_button_click)
        open_file_button.setCheckable(True)
        toolbar.addAction(open_file_button)

        # set the status bar
        self.MainWindow.setStatusBar(QStatusBar(self))

        # path for an empty big image
        start_big_image_path = 'final-year-project-danwhitehall/images/no_image_icon.png'

        # create a label and pixmap for the big image
        self.big_image_label = QLabel(self)
        self.big_label_width = int(3*(self.window_width)/4)
        self.big_label_height = int(2*(self.window_height)/3)
        self.big_image_label.setGeometry(0, 0, self.big_label_width, self.big_label_height) 
        self.big_image_label.setStyleSheet("QLabel { border: 1px solid black; }")
        self.big_image_pixmap = QPixmap(start_big_image_path)
        self.big_image_pixmap_resize = self.big_image_pixmap.scaled(100,100)
        self.big_image_label.setPixmap(self.big_image_pixmap_resize)
        # add the big image to layout
        # layout.addWidget(self.big_image_label)

        # set layout as current layout
        # self.setLayout(layout)
        self.show()

    # function when user wants to open file
    def open_file_button_click(self):
        # create a file dialog
        dialog = QFileDialog()
        dialog.setNameFilter("All images (*.png *.jpg *.tif *.tiff)")
        dialogSucessful = dialog.exec()

        # if the user has selected a file
        if dialogSucessful:
            # get the selected file
            fileInfo.selectedFiles = dialog.selectedFiles()

            # set whats in big image to the selected file
            self.big_image_pixmap = QPixmap(fileInfo.selectedFiles[0])
            self.big_image_pixmap_resize = self.big_image_pixmap.scaled(500, 500)
            self.big_image_label.setPixmap(self.big_image_pixmap_resize)
         
        # if the user didn't select a file then print this
        else:
            print("User called file dialog")

