![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/github/license/Rick45/photo-location-updater)

# Photo Location Updater (EXIF GPS Data Editor)
A simple tool to seamlessly update the geolocation metadata of your photos using an intuitive map-based interface. Whether you need to correct or add location data, this app makes it easy.


## Warning

**Important:** This tool results in data modification. It is highly recommended that a data backup be performed before executing the script. The script's author is not responsible for any data loss or damage that may occur during the execution of this script.

## Features
- 📂 Select a folder containing photos
- 🌍 View and update photo geolocation on an interactive map
- 🤖 Automate geolocation updates using Google Takeout data
- 💾 Save updated metadata easily


![app](./src/sample.png)



## App Execution 

There are two ways to run the app.

1. By downloading the executable and running it directly on your system. **Important:** Windows could say the app is unverified.

2. By downloading this repository and running it from the source code.



## Execution with .exe

1. Download the executable file from the [Releases](https://github.com/Rick45/photo-location-updater/releases) tab.

2. Extract to your desired folder **Important:** you need to extract all the content (both EXE and folder).

3. Run the "Photo Location Updater.exe" file


## Execution by source code

### Requirements

- Python 3.6+

## Installation (via source)
1. Clone the repository:
    ```bash
    git clone https://github.com/Rick45/photo-location-updater.git
    ```
2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    venv\Scripts\activate     # On Windows
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the app:
    ```bash
    python main.py
    ```

## App Usage

1. Use the GUI to select a folder containing photos.

2. Select a photo from the list to view it and its current geolocation.

3. Click on the map to update the geolocation of the selected photo.

4. Save the updated geolocation metadata to the photo.

Optionally you can load the google takeout files using the Enable Google Takeout button. When a file from the list is selected, the app will use it to find the location with the date closest to the photo taken date. Google shares the location history by month, so you will need to know the month when the photo was taken.



## How to Request Location Data from Google Takeout
Google changed the Location History data to be available only on the mobile device, this now needs to be done on the google maps app:

1. Google Maps home screen 
2. Profile picture (top right)
3. Settings
4. Google location settings
5. Location Services
6. Timeline
7. Export Timeline data

This will give you a big Json file, when firt loading it the app will ask you to split it by month. This is advised as using the full file have all you location history and the apps takes some time to run it to find the closest location.
The app will keep te original file untouched but will generate a new folder with a file structure of an folder with the year and one file by each month.

After successfully selecting and loading a takeout file the map will now show a new icon with a question mark (?) with the locationt closest to the date where the photo was taken. 

![app](./src/calculated_location.jpg)


## Acknowledgements

This project would not have been possible without the OpenStreetMap:

- [OpenStreetMap](https://www.openstreetmap.org/)

Keywords

    Exif GPS Editor
    Geotagging Tool
    Photo Metadata Editor
    Update Photo Coordinates
    EXIF Metadata

## Thanks
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/rick45)
