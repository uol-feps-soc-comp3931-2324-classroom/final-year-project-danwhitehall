# imports
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction, QIcon, QImage, QPalette
from PyQt6.sip import voidptr
from file_info import fileInfo


# main window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set all properties
        self.setObjectName("main")

        # set up the screen and add all menus
        self.setProperties()
        self.createImageLabel()
        self.createInfoBar()
        self.createToolBar()
        self.createSideMenu()

        # show window
        self.show()

    # set properties of main window
    def setProperties(self):
        self.setStyleSheet("QMainWindow#main { background-color: #CDD3D5; }")
        self.setMinimumSize(300,200)
        self.setWindowTitle("Data acquisition pipeline")
        self.showMaximized()
    
    # create label for image
    def createImageLabel(self):
        self.big_image_label = QLabel(self)
        self.big_image_label.image = QImage()
        self.big_image_label.original_image = self.big_image_label.image
        self.big_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

        self.big_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.big_image_label.setScaledContents(True)
        self.big_image_label.setPixmap(QPixmap().fromImage(self.big_image_label.image))
        self.big_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.big_image_label.resize(self.big_image_label.pixmap().size())

        # add a scroll area if label is bigger than screen size
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.big_image_label)

        self.setCentralWidget(self.scroll_area)

        
    # create the information bar at top of window
    def createInfoBar(self):
        menu = self.menuBar()

        self.open_file = QAction("Open File", self)
        self.open_file.triggered.connect(self.open_file_button_click)

        self.save_file = QAction("Save File", self)
        # TODO: self.save_file.triggered.connect(self.open_file_button_click)
        self.save_file.setEnabled(False)

        file_menu = menu.addMenu("File")
        file_menu.addAction(self.open_file)
        file_menu.addAction(self.save_file)

    # create toolbar below information bar
    def createToolBar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # create open file button for toolbar
        open_file_button = QAction("Open File", self)
        open_file_button.setStatusTip("Open a file")
        open_file_button.triggered.connect(self.open_file_button_click)
        open_file_button.setCheckable(True)
        toolbar.addAction(open_file_button)

        # set the status bar
        self.setStatusBar(QStatusBar(self))


    # create a side menu for editing image
    def createSideMenu(self):
        self.side_menu = QDockWidget("Side Menu")
        self.side_menu.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.side_menu.setMinimumWidth(100)

        container = QWidget()

        self.side_menu.setWidget(container)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.side_menu)



    # function when user wants to open file
    def open_file_button_click(self):
        # create a file dialog
        dialog = QFileDialog()
        dialog.setNameFilter("All images (*.png *.jpg *jpeg *.tif *.tiff)")
        dialogSucessful = dialog.exec()

        # if the user has selected a file
        if dialogSucessful:
            # get the selected file
            fileInfo.selectedFiles = dialog.selectedFiles()

            # set whats in big image to the selected file
            self.big_image_label.image = QImage(fileInfo.selectedFiles[0])
            self.big_image_label.setPixmap(QPixmap().fromImage(self.big_image_label.image))
            self.big_image_label.resize(self.big_image_label.pixmap().size())
         
        # if the user didn't select a file then print this
        else:
            print("User called file dialog")





# main
if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec())