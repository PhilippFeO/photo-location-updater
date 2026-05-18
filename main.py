import os
import sys
import json
import time
import urllib.request
import urllib.error
from metadataHandler import get_image_metadata, apply_metadata_to_image
from locationHistoryLoader import parse_json_file_v2, get_closest_location_v2, get_file_size
from googleTakeOutSplitter import splitGoogleTakeOut
from design import Ui_MainWindow
from PyQt6.QtCore import QEvent, pyqtSignal, pyqtSlot, QObject, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTreeWidgetItem
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QProgressDialog
from contactDialog import *

#global vars
selectedCoordinates = None
selectedLocationData = None
previousCoordinates = None
previousLocationData = None
originalCoordinates = None
takeoutClosestLocation = None
takeOutData = None

class Handler(QObject):
    coordinates_received = pyqtSignal(float, float, str, str)

    @pyqtSlot(float, float)
    @pyqtSlot(float, float, str, str)
    def receiveCoordinates(self, lat, lng, city='', country=''):
        self.coordinates_received.emit(lat, lng, city or '', country or '')

#.\photoLocationUpdaterEnv\Scripts\activate
class Window(QMainWindow, Ui_MainWindow):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        QImageReader.setAllocationLimit(0)

        # Set up the QWebChannel
        self.channel = QWebChannel()
        self.handler = Handler()
        self.channel.registerObject('handler', self.handler)
        self.mapViewWidget.page().setWebChannel(self.channel)


        self.gpsFilesListWidget.hide()
        self.clearGoogleTakeOutButton.hide()
        self.imageLeafItems = []
        self._reverse_geocode_cache = {}
        self._isUpdatingCheckState = False
        self._originalPixmap = None

        self.imageViewWidget.installEventFilter(self)

        self.fileListWidget.setColumnCount(3)
        self.fileListWidget.setHeaderLabels(["Name", "Latitude", "Longitude"])
        self.fileListWidget.header().setStretchLastSection(False)
        self.fileListWidget.header().resizeSection(0, 120)
        self.fileListWidget.header().resizeSection(1, 85)
        self.fileListWidget.header().resizeSection(2, 85)

        self.folderSelectButton.clicked.connect(self.select_folder)

        self.handler.coordinates_received.connect(self.handle_coordinates)

        self.SaveButton.clicked.connect(self.handle_saveButton)

        self.applyPreviousButton.clicked.connect(self.handle_applyPreviousButton)

        self.nextButton.clicked.connect(self.handle_nextButton)
        self.previousButton.clicked.connect(self.handle_previousButton)
        
        self.actionAbout.triggered.connect(self.show_contact_info)

        self.applyPrevSaveNext.clicked.connect(self.handle_applyPrevSaveNextButton)
        
        self.applyToAllOutButton.clicked.connect(self.handle_applyToAllOutButton)

        self.googleTakeOutButton.clicked.connect(self.select_folderTakeOutFile)

        self.clearGoogleTakeOutButton.clicked.connect(self.select_clearTakoutFile)
        
        self.reverseGeocodeButton.clicked.connect(self.handle_reverseGeocodeButton)
        ##############################image
        
        # Connect the item click event to a method
        self.fileListWidget.itemClicked.connect(self.on_file_item_clicked)
        self.fileListWidget.itemChanged.connect(self.handle_file_item_changed)

        self.gpsFilesListWidget.itemClicked.connect(self.loadTakeOutFile)

    
    def handle_applyToAllOutButton(self):
        """
        Handles the action when the "Apply to All" button is clicked.
        This function applies the selected coordinates to all images in the file list widget.
        It iterates through each item in the file list widget, retrieves its metadata, and applies the selected coordinates to each image.
        If no coordinates are selected, it displays an alert message.
        """
        global selectedCoordinates
        global selectedLocationData
        if selectedCoordinates is not None:
            targets = self._get_checked_image_items()
            if not targets:
                targets = list(self.imageLeafItems)
            total_items = len(targets)
            if total_items == 0:
                self.createAlert("No images loaded.")
                return
            
            # Create a progress dialog
            progress_dialog = QProgressDialog("Applying coordinates to all images...", "Cancel", 0, total_items, self)
            progress_dialog.setWindowTitle("Processing")
            progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress_dialog.setValue(0)
            progress_dialog.show()
    
            for i, item in enumerate(targets):
                if progress_dialog.wasCanceled():
                    self.createAlert("Operation canceled by the user.")
                    break
    
                imagePath = self._get_item_path(item)
                metadata = get_image_metadata(imagePath)
                metadata['GPSLatitude'] = selectedCoordinates[0]
                metadata['GPSLongitude'] = selectedCoordinates[1]
                if selectedLocationData:
                    if selectedLocationData.get('City'):
                        metadata['City'] = selectedLocationData['City']
                    if selectedLocationData.get('Country'):
                        metadata['Country'] = selectedLocationData['Country']
                apply_metadata_to_image(imagePath, metadata)
    
                # Update progress
                progress_dialog.setValue(i + 1)
    
            progress_dialog.close()
            self.createAlert("All images have been updated with the selected coordinates.")
        else:
            self.createAlert("No Coordinates selected.")
            return

    def select_clearTakoutFile(self):
        global takeOutData
        takeOutData = None
        self.gpsFilesListWidget.hide()
        self.gpsFilesListWidget.clear()        
        self.clearGoogleTakeOutButton.hide()        
        self.show_image(self.fileListWidget.currentItem())
        self.createAlert("Takeout file cleared, no location will be calculated from the takeout file")


    def show_contact_info(self):
            dialog = ContactDialog()
            dialog.exec()

    def _reverse_geocode_coordinates(self, lat, lng):
        """
        Fetch city and country from coordinates using Nominatim API.
        Includes retry logic with exponential backoff for rate limiting.
        
        Returns: dict with 'city' and 'country' keys, or None if request fails.
        """
        max_retries = 3
        retry_delay = 2  # Start with 2 second delay
        
        for attempt in range(max_retries):
            try:
                url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}'
                req = urllib.request.Request(url, headers={'User-Agent': 'PhotoLocationUpdater/1.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    address = data.get('address', {})
                    city = address.get('city') or address.get('town') or address.get('village') or address.get('county') or 'Unknown'
                    country = address.get('country') or 'Unknown'
                    return {'city': city.strip(), 'country': country.strip()}
            except urllib.error.HTTPError as e:
                if e.code == 429:  # Too Many Requests
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    else:
                        return None
                else:
                    return None
            except (urllib.error.URLError, json.JSONDecodeError, Exception):
                return None
        
        return None

    def _get_reverse_geocode_cached(self, lat, lng):
        """Return cached reverse geocode result for coordinate or fetch and cache it."""
        key = (round(float(lat), 6), round(float(lng), 6))
        if key in self._reverse_geocode_cache:
            return self._reverse_geocode_cache[key]

        location_data = self._reverse_geocode_coordinates(key[0], key[1])
        self._reverse_geocode_cache[key] = location_data
        return location_data

    def handle_reverseGeocodeButton(self):
        """
        Reverse geocode selected images (or all if none selected) using Nominatim API.
        Uses coordinate cache so repeated coordinates do not send duplicate requests.
        """
        checked_targets = self._get_checked_image_items()
        if checked_targets:
            targets = checked_targets
        else:
            targets = self.imageLeafItems
        
        if not targets:
            self.createAlert("No images to geocode.")
            return

        current_item = self.fileListWidget.currentItem()
        current_image_path = self._get_item_path(current_item)
        refresh_folder_path = os.path.dirname(self._get_item_path(self.imageLeafItems[0])) if self.imageLeafItems else None
        
        total_items = len(targets)
        progress_dialog = QProgressDialog("Reverse geocoding images...", "Cancel", 0, total_items, self)
        progress_dialog.setWindowTitle("Reverse Geocoding")
        progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress_dialog.setValue(0)
        progress_dialog.show()
        
        geocoded_count = 0
        skipped_count = 0
        failed_count = 0
        for i, item in enumerate(targets):
            if progress_dialog.wasCanceled():
                self.createAlert("Operation canceled by the user.")
                break

            imagePath = self._get_item_path(item)
            metadata = get_image_metadata(imagePath)

            if 'GPSLatitude' not in metadata or 'GPSLongitude' not in metadata:
                skipped_count += 1
                progress_dialog.setValue(i + 1)
                QApplication.processEvents()
                continue

            lat = metadata['GPSLatitude']
            lng = metadata['GPSLongitude']
            location_data = self._get_reverse_geocode_cached(lat, lng)

            if location_data:
                metadata['City'] = location_data['city']
                metadata['Country'] = location_data['country']
                apply_metadata_to_image(imagePath, metadata)
                geocoded_count += 1
            else:
                failed_count += 1

            progress_dialog.setValue(i + 1)
            QApplication.processEvents()

            # Keep request pace safe for Nominatim. Cached hits do not call API.
            if i < total_items - 1:
                time.sleep(1.1)
        
        progress_dialog.close()

        if refresh_folder_path:
            self._refresh_image_list(refresh_folder_path, current_image_path)
        
        if geocoded_count > 0 or skipped_count > 0 or failed_count > 0:
            msg = f"Reverse geocoding complete.\nGeocoded: {geocoded_count}\nSkipped (no GPS): {skipped_count}\nFailed: {failed_count}"
            self.createAlert(msg)
        else:
            self.createAlert("No images were processed.")

    def handle_previousButton(self):
        """
        Handles the action when the previous button is clicked.

        Retrieves the current row from the fileListWidget and checks if it is valid.
        If the current row is valid, it sets the previous row as the current row and shows the image associated with the current item.
        If the current row is not valid, it sets the last row as the current row and shows the image associated with the current item.
        """
        if not self.imageLeafItems:
            return

        current_item = self.fileListWidget.currentItem()
        if current_item in self.imageLeafItems:
            current_index = self.imageLeafItems.index(current_item)
        else:
            current_index = 0

        previous_index = (current_index - 1) % len(self.imageLeafItems)
        previous_item = self.imageLeafItems[previous_index]
        self.fileListWidget.setCurrentItem(previous_item)
        self.show_image(previous_item)

    def handle_nextButton(self):
        """
        Handles the action when the next button is clicked.

        Retrieves the current row from the fileListWidget and increments it by 1.
        If the next row is within the range of the fileListWidget count, sets the current row to the next row and shows the image of the current item.
        If the next row is outside the range, sets the current row to 0 (first item) and shows the image of the current item.
        """
        if not self.imageLeafItems:
            return

        current_item = self.fileListWidget.currentItem()
        if current_item in self.imageLeafItems:
            current_index = self.imageLeafItems.index(current_item)
        else:
            current_index = -1

        next_index = (current_index + 1) % len(self.imageLeafItems)
        next_item = self.imageLeafItems[next_index]
        self.fileListWidget.setCurrentItem(next_item)
        self.show_image(next_item)


    def handle_applyPreviousButton(self):
        """
        Handles the event when the "Apply Previous" button is clicked.
        This function updates the selected coordinates with the previous coordinates if they exist.
        It removes any existing markers from the map and adds new markers for the previous and original coordinates.
        It also updates the map location to center around the previous coordinates.
        If there are no previous coordinates, it displays an alert message.
        """
        global selectedCoordinates
        global selectedLocationData
        global previousCoordinates
        global previousLocationData
        global originalCoordinates
        if previousCoordinates != None:
            selectedCoordinates = previousCoordinates
            selectedLocationData = previousLocationData
            self.mapViewWidget.page().runJavaScript("map.eachLayer(function(layer) { if (layer instanceof L.Marker) { map.removeLayer(layer); } });")
            self.mapViewWidget.page().runJavaScript("closePopup();")
            self.mapViewWidget.page().runJavaScript(f"addMarkerWithLocationData({previousCoordinates[0]}, {previousCoordinates[1]}, 'new');")
            

            if originalCoordinates != None:
                self.mapViewWidget.page().runJavaScript(f"addMarkerWithLocationData({originalCoordinates[0]}, {originalCoordinates[1]}, 'old');")
            
            #self.mapViewWidget.page().runJavaScript(f"updateMapLocation({previousCoordinates[0]}, {previousCoordinates[1]}, 15);")

            # Adjust the map view to show both markers
            if originalCoordinates:
                self.mapViewWidget.page().runJavaScript(f"""
                    var bounds = L.latLngBounds([
                        [{previousCoordinates[0]}, {previousCoordinates[1]}],
                        [{originalCoordinates[0]}, {originalCoordinates[1]}]
                    ]);
                    map.fitBounds(bounds);
                """)
            else:
                self.mapViewWidget.page().runJavaScript(f"map.setView([{previousCoordinates[0]}, {previousCoordinates[1]}], 15);")
  
        else:
            self.createAlert("No Previous Coordinates to apply")

    def createAlert(self, message):
        """
        Display a warning alert with the given message.

        Parameters:
        - message (str): The message to be displayed in the alert.

        Returns:
        - None
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(message)
        msg.setWindowTitle("Alert")
        msg.exec()

    def handle_saveButton(self):
        """
        Handles the save button action.
        This method is responsible for saving the selected image's metadata. It checks if an image is selected, and if not, it displays an alert message. If coordinates are selected, it updates the metadata with the selected coordinates and applies the metadata to the image. If no coordinates are selected, it displays an alert message. Finally, it resets the selected coordinates and calls the next button action.
        Parameters:
        - self: The current instance of the class.
        Returns:
        - None
        """
        global selectedCoordinates
        global selectedLocationData
        global previousCoordinates
        global previousLocationData
        if selectedCoordinates != None:
            previousCoordinates = selectedCoordinates
            previousLocationData = selectedLocationData
        else:
            self.createAlert("No Coordinates selected")
            return

        checked_targets = self._get_checked_image_items()
        if checked_targets:
            targets = checked_targets
        else:
            current_item = self.fileListWidget.currentItem()
            if not self._is_image_item(current_item):
                self.createAlert("No image selected")
                return
            targets = [current_item]

        total_items = len(targets)
        if total_items > 1:
            progress_dialog = QProgressDialog("Applying coordinates to selected images...", "Cancel", 0, total_items, self)
            progress_dialog.setWindowTitle("Processing")
            progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress_dialog.setValue(0)
            progress_dialog.show()
        else:
            progress_dialog = None

        for i, item in enumerate(targets):
            if progress_dialog and progress_dialog.wasCanceled():
                self.createAlert("Operation canceled by the user.")
                break

            metadata = {}
            metadata['GPSLatitude'] = selectedCoordinates[0]
            metadata['GPSLongitude'] = selectedCoordinates[1]
            if selectedLocationData:
                if selectedLocationData.get('City'):
                    metadata['City'] = selectedLocationData['City']
                if selectedLocationData.get('Country'):
                    metadata['Country'] = selectedLocationData['Country']

            imagePath = self._get_item_path(item)
            apply_metadata_to_image(imagePath, metadata)

            if progress_dialog:
                progress_dialog.setValue(i + 1)

        if progress_dialog:
            progress_dialog.close()
        
        #call next button
        selectedCoordinates= None
        selectedLocationData = None
        if not checked_targets:
            self.handle_nextButton()


    @pyqtSlot(float, float)
    @pyqtSlot(float, float, str, str)
    def handle_coordinates(self, lat, lng, city='', country=''):
        global selectedCoordinates
        global selectedLocationData
        selectedCoordinates = (lat, lng)
        selectedLocationData = {
            'City': city.strip() if city else None,
            'Country': country.strip() if country else None,
        }


    def select_folder(self):
        """
        Opens a file dialog to select a folder and displays its path.
        If a folder was selected, it calls the `list_photos` method to list photo files in the selected folder.
        Returns:
            None
        """
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')

        # If a folder was selected, display its path and list photo files
        if folder_path:
            self.list_photos(folder_path)

    def list_photos(self, folder_path):
        """
        List all photo files in the selected folder and display them in the file list widget.
        Parameters:
        - folder_path (str): The path of the folder containing the photos.
        Returns:
        None
        """
        # Clear previous items before adding new grouped entries
        self.fileListWidget.clear()
        self.imageLeafItems = []

        # List and group all photo files in the selected folder
        photo_extensions = ('.jpg', '.jpeg', '.tiff')
        grouped_items = {}
        photo_files = [file_name for file_name in sorted(os.listdir(folder_path)) if file_name.lower().endswith(photo_extensions)]

        progress_dialog = QProgressDialog("Loading image metadata...", "Cancel", 0, len(photo_files), self)
        progress_dialog.setWindowTitle("Loading Folder")
        progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.show()

        loaded_files_count = 0
        for i, file_name in enumerate(photo_files, start=1):
            if progress_dialog.wasCanceled():
                break

            image_path = os.path.join(folder_path, file_name)
            metadata = get_image_metadata(image_path)
            country = (metadata.get('Country') or 'Unknown Country').strip() if metadata.get('Country') else 'Unknown Country'
            city = (metadata.get('City') or 'Unknown City').strip() if metadata.get('City') else 'Unknown City'
            grouped_items.setdefault(country, {}).setdefault(city, []).append({
                'name': file_name,
                'path': image_path,
                'latitude': metadata.get('GPSLatitude'),
                'longitude': metadata.get('GPSLongitude')
            })

            loaded_files_count += 1
            progress_dialog.setValue(i)
            QApplication.processEvents()

        progress_dialog.close()

        if progress_dialog.wasCanceled() and loaded_files_count == 0:
            self.createAlert("Folder loading canceled.")
            return

        self._isUpdatingCheckState = True
        for country_name in sorted(grouped_items.keys()):
            country_item = QTreeWidgetItem(self.fileListWidget, [country_name, '', ''])
            country_item.setFlags(country_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
            country_item.setCheckState(0, Qt.CheckState.Unchecked)

            for city_name in sorted(grouped_items[country_name].keys()):
                city_item = QTreeWidgetItem(country_item, [city_name, '', ''])
                city_item.setFlags(city_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
                city_item.setCheckState(0, Qt.CheckState.Unchecked)

                for image_data in grouped_items[country_name][city_name]:
                    image_item = QTreeWidgetItem(city_item)
                    image_item.setText(0, image_data['name'])
                    image_item.setText(1, self._format_coordinate(image_data['latitude']))
                    image_item.setText(2, self._format_coordinate(image_data['longitude']))
                    image_item.setFlags(image_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    image_item.setCheckState(0, Qt.CheckState.Unchecked)
                    image_item.setData(0, Qt.ItemDataRole.UserRole, image_data['path'])
                    self.imageLeafItems.append(image_item)
        self._isUpdatingCheckState = False

        self.fileListWidget.expandAll()
        
        # Show the first image in the image view widget
        if self.imageLeafItems:
            first_item = self.imageLeafItems[0]
            self.fileListWidget.setCurrentItem(first_item)
            self.show_image(first_item)

    def on_file_item_clicked(self, item, column):
        if self._is_image_item(item):
            self.show_image(item)

    def handle_file_item_changed(self, item, column):
        if self._isUpdatingCheckState or column != 0:
            return

        # Parent checks should cascade to all descendants.
        if item.childCount() > 0 and item.checkState(0) != Qt.CheckState.PartiallyChecked:
            self._isUpdatingCheckState = True
            self._set_descendants_check_state(item, item.checkState(0))
            self._isUpdatingCheckState = False

        # Force parent nodes to follow child state when all children match.
        parent = item.parent()
        while parent is not None:
            checked_children = 0
            partial_children = 0
            child_count = parent.childCount()
            for i in range(child_count):
                state = parent.child(i).checkState(0)
                if state == Qt.CheckState.Checked:
                    checked_children += 1
                elif state == Qt.CheckState.PartiallyChecked:
                    partial_children += 1

            self._isUpdatingCheckState = True
            if checked_children == child_count:
                parent.setCheckState(0, Qt.CheckState.Checked)
            elif checked_children == 0 and partial_children == 0:
                parent.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            self._isUpdatingCheckState = False
            parent = parent.parent()

    def _is_image_item(self, item):
        return bool(item and item.data(0, Qt.ItemDataRole.UserRole))

    def _get_item_path(self, item):
        if not item:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def _refresh_image_list(self, folder_path, selected_path=None):
        if not folder_path:
            return

        self.list_photos(folder_path)
        if not selected_path:
            return

        for item in self.imageLeafItems:
            if self._get_item_path(item) == selected_path:
                self.fileListWidget.setCurrentItem(item)
                self.show_image(item)
                break

    def _format_coordinate(self, value):
        if value is None:
            return ""
        return f"{float(value):.6f}"

    def _get_checked_image_items(self):
        return [item for item in self.imageLeafItems if item.checkState(0) == Qt.CheckState.Checked]

    def _set_descendants_check_state(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            if child.childCount() > 0:
                self._set_descendants_check_state(child, state)

    def show_image(self, item):
        """
        Display the selected image in the image view widget and set its location on the map.
        Parameters:
        - item: The item representing the selected image.
        Returns:
        None
        """
        if not self._is_image_item(item):
            return

        # Get the full path of the selected image
        image_path = self._get_item_path(item)
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self._originalPixmap = None
            self.imageViewWidget.clear()
            return

        self._originalPixmap = pixmap
        self._update_image_preview()

        ##logic to show image in map
        metadata = get_image_metadata(image_path)
        if(metadata.__len__() == 1 and 'CreatedDate' in metadata and takeOutData != None):
            self.set_image_aproximated_location(metadata)
            return
        elif('CreatedDate' in metadata and takeOutData != None):
            self.set_image_location_and_aproximated_location(metadata,takeOutData)
        else:
            self.set_image_location(metadata)

    def _update_image_preview(self):
        if self._originalPixmap is None:
            return

        target_size = self.imageViewWidget.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled_pixmap = self._originalPixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.imageViewWidget.setPixmap(scaled_pixmap)

    def eventFilter(self, watched, event):
        if watched is self.imageViewWidget and event.type() == QEvent.Type.Resize:
            self._update_image_preview()
        return super().eventFilter(watched, event)

    def set_image_location(self, metadata):
        """
        Sets the image location on the map based on the provided metadata.

        Parameters:
        - metadata: A dictionary containing the metadata of the image.

        Returns:
        None
        """
        # Remove all existing markers
        self.mapViewWidget.page().runJavaScript("map.eachLayer(function(layer) { if (layer instanceof L.Marker) { map.removeLayer(layer); } });")
        self.mapViewWidget.page().runJavaScript("closePopup();")
        global originalCoordinates
        
        originalCoordinates = None
        # Set the image location on the map
        if 'GPSLatitude' in metadata and 'GPSLongitude' in metadata:
            lat = metadata['GPSLatitude']
            lng = metadata['GPSLongitude']
            originalCoordinates= (lat, lng)
            self.mapViewWidget.page().runJavaScript(f"updateMapLocation({lat}, {lng}, 15);")
            self.mapViewWidget.page().runJavaScript(f"addMarkerWithLocationData({lat}, {lng}, 'new');")
        else:
            self.mapViewWidget.page().runJavaScript(f"updateMapLocation(0, 0, 2);")


    def set_image_aproximated_location(self, metadata):
        closestLocation = get_closest_location_v2(takeOutData, metadata['CreatedDate'])
        if closestLocation == None:
            return
        else:
            # Remove all existing markers
            takeoutClosestLocation = closestLocation
            self.mapViewWidget.page().runJavaScript("map.eachLayer(function(layer) { if (layer instanceof L.Marker) { map.removeLayer(layer); } });")
            self.mapViewWidget.page().runJavaScript("closePopup();")
            global selectedCoordinates
            global selectedLocationData
            # Set the image location on the map
            lat = closestLocation['Latitude']
            lng = closestLocation['Longitude']
            selectedCoordinates = (lat, lng)
            selectedLocationData = None
            distanceInMinutes = round(closestLocation['DistanceInMinutes'], 2)
            self.mapViewWidget.page().runJavaScript(f"updateMapLocation({lat}, {lng}, 15);")
            # Use the new function that fetches location data automatically
            self.mapViewWidget.page().runJavaScript(f"addMarkerWithLocationData({lat}, {lng}, 'calculated');")


    def select_folderTakeOutFile(self):
        # Clear the fileListView before adding new items
        self.clearGoogleTakeOutButton.show()
        self.gpsFilesListWidget.show()
        self.gpsFilesListWidget.clear()
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        # List all photo files in the selected folder
        files_extensions = ('.json')
        firstfile = None

        for root, dirs, files in os.walk(folder_path):
            json_files = [file_name for file_name in files if file_name.lower().endswith(files_extensions)]
            if json_files:
                parent_item = QTreeWidgetItem(self.gpsFilesListWidget, [os.path.basename(root)])
                for file_name in json_files:
                    item = QTreeWidgetItem(parent_item, [file_name])
                    item.setData(0, Qt.ItemDataRole.UserRole, root+'/'+file_name)  # Store the full path
                    if firstfile is None:
                        firstfile = item
        
    def loadTakeOutFile(self, item, column):

        global takeOutData
        
        fileloaded = False
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        #file_path = QFileDialog.getOpenFileName(self, 'Select Takeout File', '', 'JSON Files (*.json)')
        if file_path:
            try:
                file_size_mb = get_file_size(file_path)
                
                if file_size_mb > 2:
                    shouldSplit = self.splitGoogleTakeoutFileAlert(f"File size of {file_size_mb:.2f} MB can take a while to process, do you want to split it by month?")
                    if shouldSplit:
                        splitGoogleTakeOut(file_path)
                        self.createAlert("Split Successful, Please select the folder again to load the files. \n Files are saved in the same folder as the original file inside a folder named TakeOutOutput")
                    else:
                        takeOutData = parse_json_file_v2(file_path)
                        fileloaded = True
                else:
                    takeOutData = parse_json_file_v2(file_path)
                    fileloaded = True
                
            except:
                self.createAlert("Invalid Takeout file")
                
            if fileloaded:
                if takeOutData != None:
                    self.createAlert("Takeout file loaded successfully, if there is no location metadata in the photo, the system will use the takeout data to get the closest location for the photo created date")
                    if self.fileListWidget.currentItem():
                        self.show_image(self.fileListWidget.currentItem())

                if takeOutData == None:
                    self.createAlert("No Data Found in the Takeout file")
            

        else:
            self.createAlert("No no file selected nothing will be processed")
            return

    

    def handle_applyPrevSaveNextButton(self):
        """
        Handles the action when the "Previous, Save, Next" button is clicked.
        This function updates the selected coordinates with the previous coordinates if they exist.
        It removes any existing markers from the map and adds new markers for the previous and original coordinates.
        It also updates the map location to center around the previous coordinates.
        If there are no previous coordinates, it displays an alert message.
        """
        self.handle_applyPreviousButton()
        self.handle_saveButton()
        
    def splitGoogleTakeoutFileAlert(self, message):
        """
        Display an alert with two options and return the selected option.

        Parameters:
        - message (str): The message to be displayed in the alert.
        - option1 (str): The text for the first option button.
        - option2 (str): The text for the second option button.

        Returns:
        - str: The text of the selected option.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(message)
        msg.setWindowTitle("Alert")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText('Yes')
        msg.button(QMessageBox.StandardButton.No).setText('No')
        
        result = msg.exec()

        if result == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def set_image_location_and_aproximated_location(self, metadata, takeoutData):
        # TODO: implement this method to show the image location and the aproximated location from the takeout file
        
        closestLocation = {}
        closestLocation = get_closest_location_v2(takeOutData, metadata['CreatedDate'])
        
        self.mapViewWidget.page().runJavaScript("map.eachLayer(function(layer) { if (layer instanceof L.Marker) { map.removeLayer(layer); } });")
        self.mapViewWidget.page().runJavaScript("closePopup();")

        # Add marker for original location with location data
        self.mapViewWidget.page().runJavaScript(f"addMarkerWithLocationData({metadata['GPSLatitude']}, {metadata['GPSLongitude']}, 'new');")

        # Add marker for calculated location with location data
        self.mapViewWidget.page().runJavaScript(f"addMarkerWithLocationData({closestLocation['Latitude']}, {closestLocation['Longitude']}, 'calculated');")

        #self.mapViewWidget.page().runJavaScript(f"updateMapLocation({previousCoordinates[0]}, {previousCoordinates[1]}, 15);")

        # Adjust the map view to show both markers
        self.mapViewWidget.page().runJavaScript(f"""
            var bounds = L.latLngBounds([
                [{metadata['GPSLatitude']}, {metadata['GPSLongitude']}],
                [{closestLocation['Latitude']}, {closestLocation['Longitude']}]
            ]);
            map.fitBounds(bounds);
        """)
    
    def buildStringMessageOfTimeDifference(self, distanceInMinutes):
        days, remainder = divmod(distanceInMinutes, 1440)  # 1440 minutes in a day
        hours, minutes = divmod(remainder, 60)
        if days > 0:
            return f"The calculated location differs from the photos taken date by {int(days)} day {int(hours):02d} hours and {int(minutes):02d} minutes."
        elif hours > 0:
            return f"The calculated location differs from the photos taken date by {int(hours):02d} hours and {int(minutes):02d} minutes."
        else:
            return f"The calculated location differs from the photos taken date by {int(minutes):02d} minutes."
  

app = QApplication(sys.argv)
window = Window()

app.setStyle("Fusion")
window.show()
app.exec()