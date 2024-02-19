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
        self.zoom_factor = 1.0
        self.select_region_checked = False
        self.regions = []


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
        self.visible = self.scroll_area.visibleRegion()

        self.setCentralWidget(self.scroll_area)

        self.big_image_label.mousePressEvent = self.get_pixel

        
    # create the information bar at top of window
    def createInfoBar(self):
        menu = self.menuBar()

        self.open_file = QAction("Open File", self)
        self.open_file.triggered.connect(self.open_file_button_click)

        self.save_file = QAction("Save File", self)
        self.save_file.triggered.connect(self.save_file_button_click)
        self.save_file.setEnabled(False)

        file_menu = menu.addMenu("File")
        file_menu.addAction(self.open_file)
        file_menu.addAction(self.save_file)


    # create toolbar below information bar
    def createToolBar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # exit screen button
        exit_button = QAction("Exit", self)
        exit_button.triggered.connect(self.close)
        toolbar.addAction(exit_button)

        # create open file button for toolbar
        open_file_button = QAction("Open File", self)
        open_file_button.setStatusTip("Open a file")
        open_file_button.triggered.connect(self.open_file_button_click)
        toolbar.addAction(open_file_button)

        zoom_in_button = QAction("Zoom In", self)
        zoom_in_button.setStatusTip("Zoom in")
        zoom_in_button.triggered.connect(self.zoom_in_button_click)
        toolbar.addAction(zoom_in_button)

        zoom_out_button = QAction("Zoom Out", self)
        zoom_out_button.setStatusTip("Zoom out")
        zoom_out_button.triggered.connect(self.zoom_out_button_click)
        toolbar.addAction(zoom_out_button)

        # set the status bar
        self.setStatusBar(QStatusBar(self))


    # create a side menu for editing image
    def createSideMenu(self):
        # create a dock widget for the side menu
        self.side_menu = QDockWidget("Side Menu")
        self.side_menu.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.side_menu.setMinimumWidth(200)

        #TODO: add minimap
        self.small_image_label = QLabel(self)
        self.small_image_label.image = QImage()
        # self.small_image_label.original_image = self.small_image_label.image
        self.small_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

        # self.small_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.small_image_label.setScaledContents(True)
        self.small_image_label.setPixmap(QPixmap().fromImage(self.small_image_label.image))
        self.small_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.small_image_label.resize(100, 100)

        # create a label for find areas button
        toggle_areas_label = QLabel("Toggle squares")

        # create a button for toggling squares in image
        toggle_areas = QToolButton(self)
        toggle_areas.setToolTip("Toggle squares in image")
        toggle_areas.clicked.connect(self.toggle_squares_pressed)

        # create a slider to see what areas to find
        rectangle_area = QLabel("Minimum area for slider")
        self.area_slider = QSlider(Qt.Orientation.Horizontal)
        self.area_slider.setRange(0, 100)
        self.area_slider.setValue(0)
        self.area_slider.setTickInterval(10)
        self.area_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.area_slider.valueChanged.connect(self.find_areas)

        # create a label for random region button
        random_region_label = QLabel("Generate random region")

        # create a button for finding random region
        random_region_button = QToolButton(self)
        random_region_button.setToolTip("Toggle squares in image")
        random_region_button.clicked.connect(self.find_random_region)

        # create a checkbox for being able to select region
        self.select_checkbox = QCheckBox()
        self.select_checkbox.setText("Select region")
        self.select_checkbox.stateChanged.connect(self.toggle_select_region)
        
        # create a grid layout for the side menu and add all widgets
        self.side_grid_layout = QGridLayout()
        self.side_grid_layout.addWidget(self.small_image_label, 0, 0)
        self.side_grid_layout.addWidget(toggle_areas_label, 1, 0)
        self.side_grid_layout.addWidget(toggle_areas, 1, 1)
        self.side_grid_layout.addWidget(rectangle_area, 2, 0)
        self.side_grid_layout.addWidget(self.area_slider, 3, 0)
        self.side_grid_layout.addWidget(random_region_label, 4, 0)
        self.side_grid_layout.addWidget(random_region_button, 4, 1)
        self.side_grid_layout.addWidget(self.select_checkbox, 5, 0)
        self.side_grid_layout.setRowStretch(7,10)
    
        container = QWidget()
        container.setLayout(self.side_grid_layout)

        self.side_menu.setWidget(container)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.side_menu)


    def toggle_select_region(self):
        if self.select_checkbox.isChecked():
            self.select_region_checked = True
            # self.big_image_label.setMouseTracking(True)
        else:
            self.select_region_checked = False
            # self.big_image_label.setMouseTracking(False)

        
    def reset_area_slider(self):
        self.area_slider.setValue(0)


    def update_area_slider(self):
        self.area_slider.setRange(0, int(self.max_value)-1)
        self.area_slider.setTickInterval(int((self.max_value)/10))
        self.side_grid_layout.addWidget(self.area_slider, 2, 0, 1, 0)


    # function to save the file
    def save_file_button_click(self):
        if not self.big_image_label.image.isNull():
            image_file, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG(*.png);;JPEG(*.jpg *.jpeg);;Tiff(*.tiff *.tif);;All Files(*.*)")
            if image_file:
                self.big_image_label.image.save(image_file)

    # function when user wants to open file
    def open_file_button_click(self):
        self.squares_pressed_count = 0
        # create a file dialog
        dialog = QFileDialog()
        dialog.setNameFilter("All images (*.png *.jpg *jpeg *.tif *.tiff)")
        dialogSucessful = dialog.exec()

        # if the user has selected a file
        if dialogSucessful:
            self.save_file.setEnabled(True)
            # get the selected file
            fileInfo.selectedFiles = dialog.selectedFiles()
            self.image_path = fileInfo.selectedFiles[0]

            # set whats in big image to the selected file
            self.big_image_label.image = QImage(self.image_path)
            self.big_image_label.original_image = self.big_image_label.image
            self.small_image_label.image = QImage(self.image_path)
            # self.small_image_label.original_image = self.small_image_label.image

            self.save_original_image_pixmap()
            self.save_small_image_pixmap()
       
            # reset the squares slider 
            self.reset_area_slider()

            # find squares for the image
            self.find_areas()
            
        # if the user didn't select a file then print this
        else:
            print("User called file dialog")


    # fucntion that find largest and most suitable areas in image
    def find_areas(self):
        if not self.big_image_label.image.isNull():
            self.img = cv.imread(self.image_path)
            height, width, channel = self.img.shape
            self.cv_width = width
            self.cv_height = height
            gray = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)
            blur = cv.medianBlur(gray, 5)

            sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpen = cv.filter2D(blur, -1, sharpen_kernel)

            canny = cv.Canny(sharpen, 0, 255, 500)            

            ret, thresh = cv.threshold(gray, 127, 255, 0)
            
            # can do either canny or threshhold for contours
            # but I prefer to use canny as there are more larger rectangles
            self.contours, hierarchy = cv.findContours(canny, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            thresh_contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            
            # draw rectangles based on slider bar
            self.areas = []
            self.coordinates = []
            for cnt in self.contours: 
                x,y,w,h = cv.boundingRect(cnt)
                area = w*h
                # area = cv.contourArea(cnt)
                if area > int(self.area_slider.value()):
                    rect = cv.minAreaRect(cnt)
                    box = cv.boxPoints(rect)
                    box = np.int0(box)
                    cv.drawContours(self.img, [box], 0, (0,0,255), 2)
                    self.areas.append(area)
                    coord = [x,y,w,h]
                    self.coordinates.append(coord)
                    cv.rectangle(self.img, (x,y), (x+w, y+h), (0,255,0), 2)
            
            self.max_index = np.argmax(self.areas)
            self.max_value = self.areas[self.max_index]

            # update slider in real time if user has selected squares
            if self.squares_pressed_count % 2 == 1: 
                self.save_cv_image_pixmap()
            self.update_area_slider()
                

    # function to find a random region of interest
    def find_random_region(self):
        self.find_all_regions()
        random_index = np.random.randint(0, len(self.regions))
        #TODO: add a new window to show the random region of interest
        cv.imshow('Random region', self.regions[random_index])


    # function that gets all regions of interest
    def find_all_regions(self):
        if (len(self.coordinates) > 0):
            for i in range(len(self.coordinates)):
                roi = self.img[self.coordinates[i][1] : self.coordinates[i][1] + self.coordinates[i][3] , self.coordinates[i][0] : self.coordinates[i][0] + self.coordinates[i][2]]
                self.regions.append(roi)


    # display cv image with rectangles shown
    def save_cv_image_pixmap(self):
        height, width, channel = self.img.shape
        bytesPerLine = 3 * width
        self.big_image_label.image = QImage(self.img.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap().fromImage(self.big_image_label.image)
        resized_pixmap = pixmap.scaled(self.scroll_area.size() * self.zoom_factor, Qt.AspectRatioMode.KeepAspectRatio)
        self.big_image_label.setPixmap(resized_pixmap)
        self.big_image_label.resize(self.big_image_label.pixmap().size())

    
    
    # display original image with no rectangles shown
    def save_original_image_pixmap(self):
        pixmap = QPixmap().fromImage(self.big_image_label.original_image)
        resized_pixmap = pixmap.scaled(self.scroll_area.size() * self.zoom_factor, Qt.AspectRatioMode.KeepAspectRatio)
        self.big_image_label.setPixmap(resized_pixmap)
        self.big_image_label.resize(self.big_image_label.pixmap().size())


    def save_small_image_pixmap(self):
        print("1")
        pixmap = QPixmap().fromImage(self.small_image_label.image)
        resized_pixmap = pixmap.scaled(self.side_menu.width(), self.side_menu.width(), Qt.AspectRatioMode.KeepAspectRatio)
        self.small_image_label.setPixmap(resized_pixmap)
        self.small_image_label.resize(self.small_image_label.pixmap().size())
        print("2")


    # toggle screen to show squares on and off        
    def toggle_squares_pressed(self):
        if not self.big_image_label.image.isNull():
            self.squares_pressed_count += 1
            if self.squares_pressed_count % 2 == 0:
                # self.reset_area_slider()
                self.save_original_image_pixmap()
            else:
                self.save_cv_image_pixmap()

    
    # function that zooms image in
    def zoom_in_button_click(self):
        self.zoom_factor *= 1.1
        self.zoom_image()


    # function that zooms image out
    def zoom_out_button_click(self):
        self.zoom_factor *= 0.9
        self.zoom_image()

    # old version of zooming in and out
    # function that zooms image depending on if its in or out
    # def zoom_image(self):
    #     pixmap = self.big_image_label.pixmap()
    #     resized_pixmap = pixmap.scaled(self.scroll_area.size() * self.zoom_factor, Qt.AspectRatioMode.KeepAspectRatio)
    #     self.big_image_label.setPixmap(resized_pixmap)
    #     self.big_image_label.setPixmap(self.big_image_label.pixmap())
    #     self.big_image_label.resize(self.big_image_label.pixmap().size())
        

    # new version of zooming in and out
    def zoom_image(self):
        if not self.big_image_label.image.isNull():
            if self.squares_pressed_count % 2 == 0:
                self.save_original_image_pixmap()
            else:
                self.save_cv_image_pixmap()


    # function to get position of where user pressed and show this square
    def get_pixel(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.pixel_x = int((x/self.big_image_label.width()) * self.cv_width)
        self.pixel_y = int((y/self.big_image_label.height()) * self.cv_height)
        if self.select_region_checked == True:
            self.find_all_regions()
            # check if the user has clicked on a rectangle
            for i in range(len(self.coordinates)):
                if self.pixel_x > self.coordinates[i][0] and self.pixel_x < self.coordinates[i][0] + self.coordinates[i][2] and self.pixel_y > self.coordinates[i][1] and self.pixel_y < self.coordinates[i][1] + self.coordinates[i][3]:
                    cv.imshow('Random region', self.regions[i])


    #TODO: add way to use scroll to zoom in out
    #TODO: add minimap
    #TODO: click on rectangle and this goes full screen.
    #TODO: finish top and side menu    

    

# main
if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec())