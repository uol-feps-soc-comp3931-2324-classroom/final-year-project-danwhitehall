# imports
import sys
from PyQt6.QtWidgets import QToolBar
import cv2 as cv
import skimage as ski
from skimage import img_as_ubyte, io, color, filters, morphology, feature, measure
import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction, QIcon, QImage, QPalette, QPainter, QPen, QColor
from file_info import fileInfo
# time used to test time for quantitative analysis
import time


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
        self.createAcquisitionSideMenu()
        self.createInfoBar()
        self.createToolBar()

        # show window
        self.show()


    # set properties of main window
    def setProperties(self):
        self.setStyleSheet("QMainWindow#main { background-color: #CDD3D5; }")
        self.setMinimumSize(300,200)
        self.setWindowTitle("Data acquisition pipeline")
        self.showMaximized()
        self.zoom_factor_acquisition = 1.0
        self.zoom_factor_process = 1.0
        self.select_region_checked = True
        self.regions = []
        self.side_menu_side_selected = Qt.DockWidgetArea.LeftDockWidgetArea
        self.main_tab_selected = True
        self.region_img = None
        self.circles_count = 0
        self.region_x = 0
        self.region_y = 0
        self.region_width = 0
        self.region_height = 0
        self.region_centre_x = 0
        self.region_centre_y = 0
        self.average_distance = 0
        self.clustering_coefficient = 0
        self.processing_minimap_image_label = QLabel(self)
        self.processing_minimap_image_label.image = QImage()


   # create label for image
    def createImageLabel(self):
        self.tabs = QTabWidget(self)

        # add a label for the main image
        self.big_image_label = QLabel(self)
        self.big_image_label.image = QImage()
        self.big_image_label.original_image = self.big_image_label.image
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

        ##########################################################

        # add a label for the region image
        self.region_image_label = QLabel(self)
        self.region_image_label.image = QImage()
        self.region_image_label.original_image = self.region_image_label.image
        self.region_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.region_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.region_image_label.setScaledContents(True)
        self.region_image_label.setPixmap(QPixmap().fromImage(self.region_image_label.image))
        self.region_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.region_image_label.resize(self.region_image_label.pixmap().size())

        # add a scroll area if label is bigger than screen size
        self.scroll_area_region = QScrollArea()
        self.scroll_area_region.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scroll_area_region.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area_region.setWidget(self.region_image_label)
        self.visible = self.scroll_area_region.visibleRegion()

        # add the two tabs
        self.tabs.addTab(self.scroll_area, "Main Image")
        self.tabs.addTab(self.scroll_area_region, "Region Image")
        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self.tabChanged)

        # if user has clicked on the main image
        self.big_image_label.mousePressEvent = self.choose_mouse_event
        self.big_image_label.mouseMoveEvent = self.crop_main_image_move
        self.big_image_label.mouseReleaseEvent = self.crop_main_image_release

        # if user has clicked on the region image
        self.region_image_label.mousePressEvent = self.crop_region_image_button_click
        self.region_image_label.mouseMoveEvent = self.crop_region_image_move
        self.region_image_label.mouseReleaseEvent = self.crop_region_image_release

        # if user has scrolled in the scrollbar of the region image tab
        self.scroll_area.verticalScrollBar().actionTriggered.connect(self.update_small_image)
        self.scroll_area.horizontalScrollBar().actionTriggered.connect(self.update_small_image)

        
    # create the information bar at top of window
    def createInfoBar(self):
        menu = self.menuBar()

        # add an open file button
        self.open_file = QAction("Open File", self)
        self.open_file.triggered.connect(self.open_file_button_click)

        # add a save file button
        self.save_file = QAction("Save File", self)
        self.save_file.triggered.connect(self.save_file_button_click)
        self.save_file.setEnabled(False)

        # add the buttons to the file dropdown
        file_menu = menu.addMenu("File")
        file_menu.addAction(self.open_file)
        file_menu.addAction(self.save_file)

        # add a view menu
        # view_menu = menu.addMenu("View")
        # view_menu.addAction(self.toggle_acquisition_menu)
        # view_menu.addAction(self.toggle_processing_menu)


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

        # add a zoom in button
        zoom_in_button = QAction("Zoom In", self)
        zoom_in_button.setStatusTip("Zoom in")
        zoom_in_button.triggered.connect(self.zoom_in_button_click)
        toolbar.addAction(zoom_in_button)

        # add a zoom out button
        zoom_out_button = QAction("Zoom Out", self)
        zoom_out_button.setStatusTip("Zoom out")
        zoom_out_button.triggered.connect(self.zoom_out_button_click)
        toolbar.addAction(zoom_out_button)

        # add a crop button
        self.crop_button = QAction("Crop", self)
        self.crop_button.setStatusTip("Crop image")
        self.crop_button.setCheckable(True)
        toolbar.addAction(self.crop_button)

        # set the status bar
        self.setStatusBar(QStatusBar(self))


    # create a side menu for editing image
    def createAcquisitionSideMenu(self):
        # create a dock widget for the side menu
        self.acquisition_side_menu = QDockWidget("Data Acquisition Side Menu")
        self.acquisition_side_menu.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.acquisition_side_menu.setMinimumWidth(200)

        # create a label for the minimap
        self.small_image_label = QLabel(self)
        self.small_image_label.image = QImage()
        self.small_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.small_image_label.setScaledContents(True)
        self.small_image_label.setPixmap(QPixmap().fromImage(self.small_image_label.image))
        self.small_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.select_checkbox.setChecked(True)
        self.select_checkbox.stateChanged.connect(self.toggle_select_region)

        # create a button to process whole image
        process_whole_image_label = QLabel("Process whole image")
        process_whole_image_button = QToolButton(self)
        process_whole_image_button.setToolTip("Process whole image")
        process_whole_image_button.clicked.connect(self.process_whole_image)
        
        # create a grid layout for the side menu and add all widgets
        self.acquisition_side_grid_layout = QGridLayout()
        self.acquisition_side_grid_layout.addWidget(self.small_image_label, 0, 0)
        self.acquisition_side_grid_layout.addWidget(toggle_areas_label, 1, 0)
        self.acquisition_side_grid_layout.addWidget(toggle_areas, 1, 1)
        self.acquisition_side_grid_layout.addWidget(rectangle_area, 2, 0)
        self.acquisition_side_grid_layout.addWidget(self.area_slider, 3, 0)
        self.acquisition_side_grid_layout.addWidget(random_region_label, 4, 0)
        self.acquisition_side_grid_layout.addWidget(random_region_button, 4, 1)
        self.acquisition_side_grid_layout.addWidget(self.select_checkbox, 5, 0)
        self.acquisition_side_grid_layout.addWidget(process_whole_image_label, 6, 0)
        self.acquisition_side_grid_layout.addWidget(process_whole_image_button, 6, 1)
        self.acquisition_side_grid_layout.setRowStretch(10,10)
    
        # create a container for the grid layout
        container = QWidget()
        container.setLayout(self.acquisition_side_grid_layout)
        self.acquisition_side_menu.setWidget(container)

        # add the dock widget to the main window
        self.addDockWidget(self.side_menu_side_selected, self.acquisition_side_menu)
        self.toggle_acquisition_menu = self.acquisition_side_menu.toggleViewAction()

    
    # create a side menu for processing image
    def createProcessingSideMenu(self):
        self.processing_side_menu = QDockWidget("Data Processing Side Menu")
        self.processing_side_menu.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.processing_side_menu.setMinimumWidth(200)

        # create a label for the minimap
        self.processing_minimap_image_label = QLabel(self)
        self.processing_minimap_image_label.image = QImage()
        self.processing_minimap_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.processing_minimap_image_label.setScaledContents(True)
        self.processing_minimap_image_label.setPixmap(QPixmap().fromImage(self.processing_minimap_image_label.image))
        self.processing_minimap_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # create a label and button for random region button
        circles_label = QLabel("Toggle circles")
        circles_button = QToolButton(self)
        circles_button.setToolTip("Toggle circles in image")
        circles_button.clicked.connect(self.toggle_circles_pressed)

        # create slider for finding circles on region
        circle_slider_label = QLabel("Threshold")
        self.circle_slider = QSlider(Qt.Orientation.Horizontal)
        self.circle_slider.setRange(0, 100)
        self.circle_slider.setValue(0)
        self.circle_slider.setTickInterval(5)
        self.circle_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.circle_slider.valueChanged.connect(self.find_circles)

        # create a label to show number of circles
        num_of_circles_label = QLabel("Number of circles found")
        self.circles_count_label = QLabel(str(self.circles_count))

        # create a label to get coordinates of the centre
        coordinates_label = QLabel("Coordinates of centre")
        self.coord_x_label = QLabel("X: ")
        self.coord_x_value = QLabel(str(self.region_centre_x))
        self.coord_y_label = QLabel("Y: ")
        self.coord_y_value = QLabel(str(self.region_centre_y))

        # create a label to get width and height of region
        width_height_label = QLabel("Width and height of region")
        self.width_label = QLabel("Width: ")
        self.width_value = QLabel(str(self.region_width))
        self.height_label = QLabel("Height: ")
        self.height_value = QLabel(str(self.region_height))

        # create a button to claculate average distance and clustering coefficient
        calculate_button = QToolButton(self)
        calculate_button.setText("Calculate below")
        calculate_button.setToolTip("Calculate average distance and clustering coefficient")
        calculate_button.clicked.connect(self.save_processing_calculations)

        # create label for average distance between circles
        average_distance_label = QLabel("Average distance: ")
        self.average_distance_label = QLabel(str(self.average_distance))

        # create a label for clustering coefficient
        clustering_coefficient_label = QLabel("Clustering coefficient: ")
        self.clustering_coefficient_label = QLabel(str(self.clustering_coefficient))

        # create a grid layout for the side menu and add all widgets
        self.processing_side_grid_layout = QGridLayout()
        self.processing_side_grid_layout.addWidget(self.processing_minimap_image_label, 0, 0)
        self.processing_side_grid_layout.addWidget(circles_label, 1, 0)
        self.processing_side_grid_layout.addWidget(circles_button, 1, 1)
        self.processing_side_grid_layout.addWidget(circle_slider_label, 2, 0)
        self.processing_side_grid_layout.addWidget(self.circle_slider, 3, 0)
        self.processing_side_grid_layout.addWidget(num_of_circles_label, 4, 0)
        self.processing_side_grid_layout.addWidget(self.circles_count_label, 4, 1)
        self.processing_side_grid_layout.addWidget(coordinates_label, 5, 0)
        self.processing_side_grid_layout.addWidget(self.coord_x_label, 6, 0)
        self.processing_side_grid_layout.addWidget(self.coord_x_value, 6, 1)
        self.processing_side_grid_layout.addWidget(self.coord_y_label, 7, 0)
        self.processing_side_grid_layout.addWidget(self.coord_y_value, 7, 1)
        self.processing_side_grid_layout.addWidget(width_height_label, 8, 0)
        self.processing_side_grid_layout.addWidget(self.width_label, 9, 0)
        self.processing_side_grid_layout.addWidget(self.width_value, 9, 1)
        self.processing_side_grid_layout.addWidget(self.height_label, 10, 0)
        self.processing_side_grid_layout.addWidget(self.height_value, 10, 1)
        self.processing_side_grid_layout.addWidget(calculate_button, 11, 0)
        self.processing_side_grid_layout.addWidget(average_distance_label, 12, 0)
        self.processing_side_grid_layout.addWidget(self.average_distance_label, 12, 1)
        self.processing_side_grid_layout.addWidget(clustering_coefficient_label, 13, 0)
        self.processing_side_grid_layout.addWidget(self.clustering_coefficient_label, 13, 1)
        self.processing_side_grid_layout.setRowStretch(20, 10)
        container = QWidget()
        container.setLayout(self.processing_side_grid_layout)
        self.processing_side_menu.setWidget(container)

        self.addDockWidget(self.side_menu_side_selected, self.processing_side_menu)
        self.toggle_processing_menu = self.processing_side_menu.toggleViewAction()


    # function to chage the side menus when tab is changed
    def tabChanged(self, index):
        if self.main_tab_selected == True:
            self.side_menu_side_selected = self.dockWidgetArea(self.acquisition_side_menu)
            self.removeDockWidget(self.acquisition_side_menu)
            self.createProcessingSideMenu()
            self.update_processing_minimap()
            self.update_coordinates_and_dimensions()
            self.main_tab_selected = False
            self.find_circles()
        else:
            self.side_menu_side_selected = self.dockWidgetArea(self.processing_side_menu)
            self.removeDockWidget(self.processing_side_menu)
            self.createAcquisitionSideMenu()
            self.update_small_image()
            self.main_tab_selected = True


    # function used when user toggles select squares button
    def toggle_select_region(self):
        if self.select_checkbox.isChecked():
            self.select_region_checked = True
        else:
            self.select_region_checked = False

    
    # function to reset area slider
    def reset_area_slider(self):
        self.area_slider.setValue(0)


    # function to update area slider
    def update_area_slider(self):
        self.area_slider.setRange(0, int(self.max_value)-1)
        self.area_slider.setTickInterval(int((self.max_value)/10))


    # function to save the file
    def save_file_button_click(self):
        if not self.region_image_label.image.isNull():
            image_file, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG(*.png);;JPEG(*.jpg *.jpeg);;Tiff(*.tiff *.tif);;All Files(*.*)")
            if image_file:
                try:
                    pixmap = self.region_image_label.pixmap()
                    pixmap.save(image_file)
                    print("Image saved successfully!")
                except Exception as e:
                    print("Error saving image:", e)
        else:
            print("No image to save")


    # function when user wants to open file
    def open_file_button_click(self):
        self.squares_pressed_count = 0
        self.circles_pressed_count = 0
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
            self.processing_minimap_image_label.image = QImage(self.image_path)

            # save the image to both main image and minimap
            self.save_original_image_pixmap()
            self.save_small_image_pixmap()
       
            # reset the squares slider 
            self.reset_area_slider()

            # find squares for the image
            self.find_areas()
            self.update_small_image()
            
        # if the user didn't select a file then print this
        else:
            print("User called file dialog")


    # fucntion that find largest and most suitable areas in image
    def find_areas(self):
        if not self.big_image_label.image.isNull():
            self.img = cv.imread(self.image_path)
            self.img_copy = self.img.copy()
            height, width, channel = self.img_copy.shape
            self.cv_width = width
            self.cv_height = height

            # preprocess the image
            gray = cv.cvtColor(self.img_copy, cv.COLOR_BGR2GRAY)
            blur = cv.medianBlur(gray, 5)
            sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpen = cv.filter2D(blur, -1, sharpen_kernel)

            # find the edges
            canny = cv.Canny(sharpen, 0, 255, 500)            

            # ret, thresh = cv.threshold(gray, 127, 255, 0)
            
            # can do either canny or threshhold for contours
            # but I prefer to use canny as there are more larger rectangles
            self.contours, hierarchy = cv.findContours(canny, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            # thresh_contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            
            # draw rectangles based on slider bar
            self.areas = []
            self.coordinates = []
            for cnt in self.contours: 
                x,y,w,h = cv.boundingRect(cnt)
                area = w*h
                if area > int(self.area_slider.value()):
                    rect = cv.minAreaRect(cnt)
                    box = cv.boxPoints(rect)
                    box = np.int0(box)
                    cv.drawContours(self.img_copy, [box], 0, (0,0,255), 2)
                    self.areas.append(area)
                    coord = [x,y,w,h,area]
                    self.coordinates.append(coord)
                    cv.rectangle(self.img_copy, (x,y), (x+w, y+h), (0,255,0), 2)
                    
            # sort the areas and coordinates
            self.coordinates = sorted(self.coordinates, key=lambda x: x[4])
            self.max_index = np.argmax(self.areas)
            self.max_value = self.areas[self.max_index]

            # update slider in real time if user has selected squares
            if self.squares_pressed_count % 2 == 1: 
                self.save_cv_image_pixmap()
            self.update_area_slider()


    # function to find connected components
    def connected_components(self, image, connectivity=2):
        labeled_image, count = ski.measure.label(self.binary_mask,
                                                    connectivity=connectivity, return_num=True)
        return labeled_image, count
    

    # this method finds more variety of radius but when two circles
    # next to each other they are merged into one circle
    def find_circles(self):
        if self.region_img is not None:
            # preprocess image
            gray_image = color.rgb2gray(self.region_img)

            # get binary mask
            t = float(self.circle_slider.value())/100
            self.binary_mask = gray_image < t
            self.binary_mask = morphology.binary_erosion(self.binary_mask, morphology.disk(0))

            # find circles
            labeled_mask = measure.label(self.binary_mask)
            self.circle_regions = measure.regionprops(labeled_mask)

            if self.circles_pressed_count % 2 == 1: 
                self.save_image_with_circles()


    # save the region image with circles drawn on it
    def save_image_with_circles(self):
        if self.region_img is not None:
            region_bytes = self.region_img.tobytes()
            height, width, channel = self.region_img.shape
            bytesPerLine = 3 * width
            self.region_image_label.image = QImage(region_bytes, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            pixmap = QPixmap().fromImage(self.region_image_label.image)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # draw the circles
            for region in self.circle_regions:
                centroid_y, centroid_x = region.centroid
                radius = np.sqrt(region.area / np.pi)
                painter.setPen(QPen(QColor("red"), 2))
                painter.drawEllipse(int(centroid_x - radius), int(centroid_y - radius), int(2 * radius), int(2 * radius))
            
            self.circles_count = len(self.circle_regions)
            self.update_circle_count()
            painter.end()
            resized_pixmap = pixmap.scaled(self.scroll_area_region.size() * self.zoom_factor_process, Qt.AspectRatioMode.KeepAspectRatio)

            # Display the QPixmap
            self.region_image_label.setPixmap(resized_pixmap)
            self.region_image_label.resize(self.region_image_label.pixmap().size())


    # save the calculations and show to user
    def save_processing_calculations(self):
        if self.region_img is not None:
            distances = []
            for i in range(len(self.circle_regions)):
                for j in range(i+1, len(self.circle_regions)):
                    distance = np.sqrt((self.circle_regions[i].centroid[0] - self.circle_regions[j].centroid[0])**2 +
                                       (self.circle_regions[i].centroid[1] - self.circle_regions[j].centroid[1])**2)
                    distances.append(distance)
            self.average_distance = np.mean(distances)

            self.clustering_coefficient = (self.circles_count * self.average_distance) / (2 * self.region_width * self.region_height)
            self.average_distance_label.setText(str(self.average_distance))
            self.clustering_coefficient_label.setText(str(self.clustering_coefficient))
                

    # gets each specific circle but radii is one of 4 options
    # NOTE - this is method 2 used in chapter 3.3.2
    # def find_circles3(self):
    #     if self.region_img is not None:
    #         gray_image = color.rgb2gray(self.region_img)
    #         t = float(self.circle_slider.value())/100
    #         self.binary_mask = gray_image < t
    #         self.binary_mask = morphology.binary_closing(self.binary_mask, morphology.disk(3))
    #         blobs = feature.blob_log(self.binary_mask, min_sigma=5, max_sigma=30, threshold=0.1)
    #         centers = blobs[:, :2]
    #         radii = blobs[:, 2] * np.sqrt(2)
    #         self.circles_count = len(centers)

    #         distances = []
    #         for i in range(len(centers)):
    #             for j in range (i+1, len(centers)):
    #                 distance = np.sqrt((centers[i][0] - centers[j][0])**2 + (centers[i][1] - centers[j][1])**2)
    #                 distances.append(distance)
    #         self.average_distance = np.mean(distances)
    #         self.clustering_coefficient = (self.circles_count * self.average_distance) / (2 * self.region_width * self.region_height)

    #         # Plot the original image with detected circles
    #         fig, ax = plt.subplots()
    #         ax.imshow(self.region_img, cmap='gray')
    #         for center, radius in zip(centers, radii):
    #             circle = plt.Circle((center[1], center[0]), radius, color='red', fill=False)
    #             ax.add_patch(circle)
    #         # Display the plot
    #         plt.show()

        
    # update the number of elements
    def update_circle_count(self):
        self.circles_count_label.setText(str(self.circles_count))


    # update acquisition minimap
    def update_small_image(self):
        if self.big_image_label.image.isNull():
            return
        viewport_copy = self.img.copy()
        height, width, channel = viewport_copy.shape
        bytesPerLine = 3 * width

        total_height = self.scroll_area.widget().height()
        viewport_height = self.scroll_area.viewport().height()
        vertical_scrollbar_value = self.scroll_area.verticalScrollBar().value()

        total_width = self.scroll_area.widget().width()
        viewport_width = self.scroll_area.viewport().width()
        horizontal_scrollbar_value = self.scroll_area.horizontalScrollBar().value()

        if total_height == 0 or total_width == 0:
            return

        height_ratio = viewport_height / total_height
        width_ratio = viewport_width / total_width

        minimap_viewport_height = int(height_ratio * height)
        minimap_viewport_width = int(width_ratio * width)
        minimap_viewport_y_position = int((vertical_scrollbar_value / total_height) * height)
        minimap_viewport_x_position = int((horizontal_scrollbar_value / total_width) * width)
        cv.rectangle(viewport_copy, (minimap_viewport_x_position, minimap_viewport_y_position), (minimap_viewport_x_position + minimap_viewport_width, minimap_viewport_y_position + minimap_viewport_height), (0,255,0), 10)
        self.small_image_label.image = QImage(viewport_copy.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap().fromImage(self.small_image_label.image)
        resized_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
        self.small_image_label.setPixmap(resized_pixmap)


    # update processing minimap
    def update_processing_minimap(self):
        if self.region_img is not None:
            viewport_copy = self.img.copy()
            height, width, channel = viewport_copy.shape
            bytesPerLine = 3 * width
            cv.rectangle(viewport_copy, (self.region_x, self.region_y), (self.region_x + self.region_width, self.region_y + self.region_height), (0,255,0), 10)
            self.processing_minimap_image_label.image = QImage(viewport_copy.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            pixmap = QPixmap().fromImage(self.processing_minimap_image_label.image)
            resized_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            self.processing_minimap_image_label.setPixmap(resized_pixmap)


    # function to process whole image into process tab
    def process_whole_image(self):
        if not self.big_image_label.image.isNull():
            self.region_img = self.img
            self.region_x = 0
            self.region_y = 0
            self.region_width = self.cv_width
            self.region_height = self.cv_height
            
            self.save_cv_region_image_pixmap()
            self.update_processing_minimap()

                
    # function to find a random region of interest
    def find_random_region(self):
        if not self.big_image_label.image.isNull():
            self.find_all_regions()
            random_index = np.random.randint(0, len(self.regions))
            self.region_img = self.regions[random_index]
            self.region_x = self.coordinates[random_index][0]
            self.region_y = self.coordinates[random_index][1]
            self.region_width = self.coordinates[random_index][2]
            self.region_height = self.coordinates[random_index][3]
            self.save_cv_region_image_pixmap()
            self.update_processing_minimap()


    # function that gets all regions of interest
    def find_all_regions(self):
        if (len(self.coordinates) > 0):
            self.regions = []
            for i in range(len(self.coordinates)):
                roi = self.img[self.coordinates[i][1] : self.coordinates[i][1] + self.coordinates[i][3] , self.coordinates[i][0] : self.coordinates[i][0] + self.coordinates[i][2]]
                self.regions.append(roi)


    # display cv image with rectangles shown
    def save_cv_image_pixmap(self):
        height, width, channel = self.img_copy.shape
        bytesPerLine = 3 * width
        self.big_image_label.image = QImage(self.img_copy.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixmap = QPixmap().fromImage(self.big_image_label.image)
        resized_pixmap = pixmap.scaled(self.scroll_area.size() * self.zoom_factor_acquisition, Qt.AspectRatioMode.KeepAspectRatio)
        self.big_image_label.setPixmap(resized_pixmap)
        self.big_image_label.resize(self.big_image_label.pixmap().size())
    
    
    # display original image with no rectangles shown
    def save_original_image_pixmap(self):
        pixmap = QPixmap().fromImage(self.big_image_label.original_image)
        resized_pixmap = pixmap.scaled(self.scroll_area.size() * self.zoom_factor_acquisition, Qt.AspectRatioMode.KeepAspectRatio)
        self.big_image_label.setPixmap(resized_pixmap)
        self.big_image_label.resize(self.big_image_label.pixmap().size())


    # display updated acquisition minimap
    def save_small_image_pixmap(self):
        pixmap = QPixmap().fromImage(self.small_image_label.image)
        resized_pixmap = pixmap.scaled(self.acquisition_side_menu.width(), self.acquisition_side_menu.width(), Qt.AspectRatioMode.KeepAspectRatio)
        self.small_image_label.setPixmap(resized_pixmap)
        self.small_image_label.resize(self.small_image_label.pixmap().size())


    # display updated processing minimap    
    def save_processing_minimap_pixmap(self):
        pixmap = QPixmap().fromImage(self.processing_minimap_image_label.image)
        resized_pixmap = pixmap.scaled(self.processing_side_menu.width(), self.processing_side_menu.width(), Qt.AspectRatioMode.KeepAspectRatio)
        self.processing_minimap_image_label.setPixmap(resized_pixmap)
        self.processing_minimap_image_label.resize(self.processing_minimap_image_label.pixmap().size())


    # save region image
    def save_cv_region_image_pixmap(self):
        if self.region_img is not None:
            region_bytes = self.region_img.tobytes()
            height, width, channel = self.region_img.shape
            bytesPerLine = 3 * width

            self.region_image_label.image = QImage(region_bytes, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            pixmap = QPixmap().fromImage(self.region_image_label.image)
            resized_pixmap = pixmap.scaled(self.scroll_area_region.size() * self.zoom_factor_process, Qt.AspectRatioMode.KeepAspectRatio)

            self.region_image_label.setPixmap(resized_pixmap)
            self.region_image_label.resize(self.region_image_label.pixmap().size())
            self.tabs.setCurrentIndex(1)


    # toggle screen to show squares on and off        
    def toggle_squares_pressed(self):
        if not self.big_image_label.image.isNull():
            self.squares_pressed_count += 1
            if self.squares_pressed_count % 2 == 0:
                # self.reset_area_slider()
                self.save_original_image_pixmap()
            else:
                self.save_cv_image_pixmap()

    
    # toggle screen to show circles on and off
    def toggle_circles_pressed(self):
        if self.region_img is not None:
            self.circles_pressed_count += 1
            if self.circles_pressed_count % 2 == 0:
                self.save_cv_region_image_pixmap()
            else:
                self.save_image_with_circles()

    
    # function that zooms image in
    def zoom_in_button_click(self):
        if self.main_tab_selected == True:
            self.zoom_factor_acquisition *= 1.1
        else:
            self.zoom_factor_process *= 1.1
        self.zoom_image()
        

    # function that zooms image out
    def zoom_out_button_click(self):
        if self.main_tab_selected == True:
            self.zoom_factor_acquisition *= 0.9
        else:
            self.zoom_factor_process *= 0.9
        self.zoom_image()


    # new version of zooming in and out
    def zoom_image(self):
        if self.main_tab_selected == True:
            if not self.big_image_label.image.isNull():
                if self.squares_pressed_count % 2 == 0:
                    self.save_original_image_pixmap()
                else:
                    self.save_cv_image_pixmap()
                self.update_small_image()
        else:
            if self.region_img is not None:
                if self.circles_pressed_count % 2 == 0:
                    self.save_cv_region_image_pixmap()
                else:
                    self.save_image_with_circles()
                self.update_processing_minimap()


    # function that chooses whether to crop image or select region
    def choose_mouse_event(self, event):
        if self.crop_button.isChecked():
            self.big_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.big_image_label)
            self.crop_main_image_button_click(event)
        else:
            self.get_pixel(event)


    # function to crop image
    def crop_main_image_button_click(self, event):
        if not self.big_image_label.image.isNull():
            self.original_point = event.pos()
            self.big_image_label.rubber_band.setGeometry(QRect(self.original_point, QSize()).normalized())
            self.big_image_label.rubber_band.show()

    
    # function to update rubber band
    def crop_main_image_move(self, event):
        if self.crop_button.isChecked():
            if not self.big_image_label.image.isNull():
                self.big_image_label.rubber_band.setGeometry(QRect(self.original_point, event.pos()).normalized())

        
    # function that gets final point of rubber band
    def crop_main_image_release(self, event):
        if self.crop_button.isChecked():
            if not self.big_image_label.image.isNull():
                self.big_image_label.rubber_band.hide()
                self.final_point = event.pos()
                self.crop_main_image()

    
    # function that crops the image
    def crop_main_image(self):
        if not self.big_image_label.image.isNull():
            self.original_pixel_x = int((self.original_point.x()/self.big_image_label.width()) * self.cv_width)
            self.original_pixel_y = int((self.original_point.y()/self.big_image_label.height()) * self.cv_height)
            self.final_pixel_x = int((self.final_point.x()/self.big_image_label.width()) * self.cv_width)
            self.final_pixel_y = int((self.final_point.y()/self.big_image_label.height()) * self.cv_height)
            if self.final_pixel_x == self.original_pixel_x or self.final_pixel_y == self.original_pixel_y:
                return
            self.region_img = self.img[self.original_pixel_y:self.final_pixel_y, self.original_pixel_x:self.final_pixel_x]
            self.save_cv_region_image_pixmap()

    
    # function that recognises start of crop
    def crop_region_image_button_click(self, event):
        if self.crop_button.isChecked():
            if self.region_img is not None:
                self.region_image_label.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.region_image_label)
                self.original_point = event.pos()
                self.region_image_label.rubber_band.setGeometry(QRect(self.original_point, QSize()).normalized())
                self.region_image_label.rubber_band.show()
    

    # function that recognises movement of crop
    def crop_region_image_move(self, event):
        if self.crop_button.isChecked():
            if self.region_img is not None:
                self.region_image_label.rubber_band.setGeometry(QRect(self.original_point, event.pos()).normalized())


    # function that recognises end of crop
    def crop_region_image_release(self, event):
        if self.crop_button.isChecked():
            if self.region_img is not None:
                self.region_image_label.rubber_band.hide()
                self.final_point = event.pos()
                self.crop_region_image()
                

    # function to crop region image
    def crop_region_image(self):
        if self.region_img is not None:
            self.original_pixel_x = int((self.original_point.x()/self.region_image_label.width()) * self.region_img.shape[1])
            self.original_pixel_y = int((self.original_point.y()/self.region_image_label.height()) * self.region_img.shape[0])
            self.final_pixel_x = int((self.final_point.x()/self.region_image_label.width()) * self.region_img.shape[1])
            self.final_pixel_y = int((self.final_point.y()/self.region_image_label.height()) * self.region_img.shape[0])
            print(self.original_pixel_x, self.original_pixel_y, self.final_pixel_x, self.final_pixel_y)
            self.region_img = self.region_img[self.original_pixel_y:self.final_pixel_y, self.original_pixel_x:self.final_pixel_x]
            self.save_cv_region_image_pixmap()


    # get coordinate of centre of region and dimensions of region
    def update_coordinates_and_dimensions(self):
        if self.region_img is not None:
            self.region_centre_x = self.region_x + (self.region_width / 2)
            self.region_centre_y = self.region_y + (self.region_height / 2)
            self.region_centre_x = self.region_centre_x / self.cv_width
            self.region_centre_y = self.region_centre_y / self.cv_height
            self.region_centre_x += -0.5
            self.region_centre_y = 0.5 - self.region_centre_y
            self.coord_x_value.setText(str(self.region_centre_x))
            self.coord_y_value.setText(str(self.region_centre_y))
            self.width_value.setText(str(self.region_width))
            self.height_value.setText(str(self.region_height))


    # function to get position of where user pressed and show this square
    def get_pixel(self, event):
        # get x and y position of where user clicked
        x = event.pos().x()
        y = event.pos().y()

        # get x, y position in relation to size of image
        self.pixel_x = int((x/self.big_image_label.width()) * self.cv_width)
        self.pixel_y = int((y/self.big_image_label.height()) * self.cv_height)

        if self.select_region_checked == True:
            self.find_all_regions()
            # check if the user has clicked on a rectangle
            for i in range(len(self.coordinates)):
                if self.pixel_x > self.coordinates[i][0] and self.pixel_x < (self.coordinates[i][0] + self.coordinates[i][2]) and self.pixel_y > self.coordinates[i][1] and self.pixel_y < (self.coordinates[i][1] + self.coordinates[i][3]):
                    self.region_img = self.regions[i]
                    self.region_x = self.coordinates[i][0]
                    self.region_y = self.coordinates[i][1]
                    self.region_width = self.coordinates[i][2]
                    self.region_height = self.coordinates[i][3]
                    self.save_cv_region_image_pixmap()
                    break

                    
    #TODO: add width and height of image to processing menu

    

# main
if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec())