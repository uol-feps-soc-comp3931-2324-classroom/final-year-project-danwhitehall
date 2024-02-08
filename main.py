# imports
import sys
from PyQt6.QtWidgets import QToolBar
import cv2 as cv
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction, QIcon, QImage, QPalette
# from PyQt6.sip import voidptr
from file_info import fileInfo



# main window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image = None

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
        # create a dock widget for the side menu
        self.side_menu = QDockWidget("Side Menu")
        self.side_menu.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.side_menu.setMinimumWidth(200)

        # create a label for find areas button
        toggle_areas_label = QLabel("Toggle squares")

        # TODO: create a button for toggling squares in image
        # create a button for finding squares in image
        toggle_areas = QToolButton(self)
        toggle_areas.setToolTip("Find areas in image")
        toggle_areas.clicked.connect(self.find_areas)

        # create a slider to see what areas to find
        rectangle_area = QLabel("Minimum area for slider")
        self.area_slider = QSlider(Qt.Orientation.Horizontal)
        self.area_slider.setRange(0, 100)
        self.area_slider.setValue(0)
        self.area_slider.setTickInterval(10)
        self.area_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        #TODO: self.area_slider.valueChanged.connect(area_slider_changed)

        # create a grid layout for the side menu and add all widgets
        self.side_grid_layout = QGridLayout()
        self.side_grid_layout.addWidget(toggle_areas_label, 0, 0, 1, 2)
        self.side_grid_layout.addWidget(toggle_areas, 0, 1, 1, 3)
        self.side_grid_layout.addWidget(rectangle_area, 1, 0)
        self.side_grid_layout.addWidget(self.area_slider, 2, 0, 1, 0)
        self.side_grid_layout.setRowStretch(7,10)
    
        container = QWidget()
        container.setLayout(self.side_grid_layout)

        self.side_menu.setWidget(container)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.side_menu)

    def area_slider_changed(self, value):
        print(value)
        #TODO: implement function where the squares get updates based on slider change
        
    def reset_area_slider(self):
        self.area_slider.setValue(0)



    def update_area_slider(self):
        self.area_slider.setRange(0, int(self.max_value)-1)
        self.area_slider.setTickInterval(int((self.max_value)/10))
        self.side_grid_layout.addWidget(self.area_slider, 2, 0, 1, 0)
        print("1")


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
            self.image_path = fileInfo.selectedFiles[0]

            # set whats in big image to the selected file
            self.big_image_label.image = QImage(self.image_path)
            pixmap = QPixmap().fromImage(self.big_image_label.image)
            self.big_image_label.setPixmap(pixmap)
           
            # reset the squares slider 
            self.reset_area_slider()

            # find squares for the image
            self.find_areas()

            # update the squares slider
            self.update_area_slider()
            
        # if the user didn't select a file then print this
        else:
            print("User called file dialog")

    # fucntion that find largest and most suitable areas in image
    def find_areas(self):
        if not self.big_image_label.image.isNull():
            self.img = cv.imread(self.image_path)
            gray = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)
            blur = cv.medianBlur(gray, 5)

            sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpen = cv.filter2D(blur, -1, sharpen_kernel)

            canny = cv.Canny(sharpen, 0, 255, 500)            

            ret, thresh = cv.threshold(gray, 127, 255, 0)
            
            # can do either canny or threshhold for contours
            # but I prefer to use canny as there are more larger rectangles
            contours, hierarchy = cv.findContours(canny, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            thresh_contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            
            # draw rectangles based on slider bar
            self.areas = []
            for cnt in contours: 
                x,y,w,h = cv.boundingRect(cnt)
                area = w*h
                # area = cv.contourArea(cnt)
                if area > int(self.area_slider.value()):
                    rect = cv.minAreaRect(cnt)
                    box = cv.boxPoints(rect)
                    box = np.int0(box)
                    cv.drawContours(self.img, [box], 0, (0,0,255), 2)
                    self.areas.append(area)
                    cv.rectangle(self.img, (x,y), (x+w, y+h), (0,255,0), 2)
            # cv.imshow('image with rectangles', self.img)
            
            self.max_index = np.argmax(self.areas)
            self.max_value = self.areas[self.max_index]

            self.save_image_pixmap()
            
            # TODO: add region of interest based on what region the user choses
            # x, y, w, h = cv.boundingRect(contours[max_index])
            # roi = img[y : y + h , x : x + w]
            # cv.imshow('ROI',roi)

    # TODO: save the image in a pixmap so it can be displayed
    def save_image_pixmap(self):
        height, width, channel = self.img.shape
        bytesPerLine = 3 * width
        self.big_image_label.image = QImage(self.img.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap().fromImage(self.big_image_label.image)
        resized_pixmap = pixmap.scaled(self.scroll_area.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.big_image_label.setPixmap(resized_pixmap)
        self.big_image_label.resize(self.big_image_label.pixmap().size())





            
            






# main
if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec())