import json
import os
from datetime import datetime
from PyQt6.QtWidgets import QProgressDialog
from PyQt6.QtCore import Qt
def splitGoogleTakeOut(file_path):
    parsed_data = googleTakeOutSplitter(file_path)
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_folder = os.path.join(os.path.dirname(file_path), f'TakeOutOutput_{current_time}')
    save_locations_by_month(parsed_data, output_folder)

def googleTakeOutSplitter(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    extracted_data = []
    for signal in data.get('rawSignals', []):
        position = signal.get('position', {})
        lat_lng = position.get('LatLng')
        timestamp = position.get('timestamp')
        if lat_lng and timestamp:
            # Remove the ° character from LatLng
            lat_lng = lat_lng.replace('Â', '')
            lat_lng = lat_lng.replace('°', '')
            # Split lat_lng into latitude and longitude
            latitude, longitude = lat_lng.split(', ')
            extracted_data.append({
                'DateTime': timestamp,
                "Latitude": float(latitude),
                "Longitude": float(longitude)
            })
    
    for segment in data.get('semanticSegments', []):
        start_time = segment.get('startTime')
        end_time = segment.get('endTime')
        timeline_path = segment.get('timelinePath', [])
        for point in timeline_path:
            point_location = point.get('point')
            point_time = point.get('time')
            if point_location and point_time:
                # Remove the ° character from point_location
                point_location = point_location.replace('Â', '')
                point_location = point_location.replace('°', '')
                # Split point_location into latitude and longitude
                latitude, longitude = point_location.split(', ')
                extracted_data.append({
                    'DateTime': point_time,
                    "Latitude": float(latitude),
                    "Longitude": float(longitude)
                })
                
        visit = segment.get('visit', {})
        if visit:
            top_candidate = visit.get('topCandidate', {})
            place_location = top_candidate.get('placeLocation', {})
            lat_lng = place_location.get('latLng')
            if lat_lng:
                # Remove the ° character from lat_lng
                lat_lng = lat_lng.replace('Â', '')
                lat_lng = lat_lng.replace('°', '')
                # Split lat_lng into latitude and longitude
                latitude, longitude = lat_lng.split(', ')
                extracted_data.append({
                    'DateTime': start_time,
                    "Latitude": float(latitude),
                    "Longitude": float(longitude)
                })
    
    return extracted_data

def save_locations_by_month(extracted_data, output_folder):
    locations_by_month = {}
    
    total_stepsA = extracted_data.__len__()
    
    progress_dialogTotals = QProgressDialog("Calculating totals...", "Cancel", 0, total_stepsA)
    progress_dialogTotals.setWindowTitle("Processing")
    progress_dialogTotals.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress_dialogTotals.show()

    stepsForTotals = 0
    for entry in extracted_data:
        date_time = entry['DateTime']
        date_obj = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S.%f%z')
        year = date_obj.year
        month = date_obj.month
        
        if year not in locations_by_month:
            locations_by_month[year] = {}
        if month not in locations_by_month[year]:
            locations_by_month[year][month] = []
        
        locations_by_month[year][month].append(entry)
        stepsForTotals += 1
        progress_dialogTotals.setValue(stepsForTotals)
        if progress_dialogTotals.wasCanceled():
            break
    
    progress_dialogTotals.close()
    
    total_steps = sum(len(months) for months in locations_by_month.values())
    progress_dialog = QProgressDialog("Saving locations...", "Cancel", 0, total_steps)
    progress_dialog.setWindowTitle("Processing")
    progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress_dialog.show()
    
    step = 0
    for year, months in locations_by_month.items():
        year_folder = os.path.join(output_folder, str(year))
        os.makedirs(year_folder, exist_ok=True)
        
        for month, locations in months.items():
            month_file_path = os.path.join(year_folder, f'{month:02d}.json')
            with open(month_file_path, 'w', encoding='utf-8') as month_file:
                json.dump({"TakeOutSplitterResult": locations}, month_file, ensure_ascii=False, indent=4)
            
            step += 1
            progress_dialog.setValue(step)
            if progress_dialog.wasCanceled():
                break

    progress_dialog.close()


