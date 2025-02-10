import json
from datetime import datetime, timezone
import re
import os


def get_file_size(file_path):
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    return file_size_mb

"""
Google changed the location history to be stored in the mobile device only.
with this change they also changed the format of the location history json file.
"""
def parse_json_file_v2(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    

    extracted_data = []

    #IF TakeOutSplitterResult is present, then the file is in the app splited format
    if 'TakeOutSplitterResult' in data:
        takeout_splitter_result = data['TakeOutSplitterResult']
        extracted_data = []
        
        for entry in takeout_splitter_result:
            date_time = entry.get('DateTime')
            latitude = entry.get('Latitude')
            longitude = entry.get('Longitude')
            
            if date_time and latitude is not None and longitude is not None:
                extracted_data.append({
                    'DateTime': date_time,
                    'Latitude': latitude,
                    'Longitude': longitude
                })
    # Is the original google takeout file
    else:
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


def get_closest_location_v2(data, target_timestamp):
    closest_location = None
    closest_distance = float("inf")
    distance = 0
    count=0
    target_datetime = datetime.strptime(target_timestamp, '%Y:%m:%d %H:%M:%S').replace(tzinfo=timezone.utc)
    for entry in data:
        entry_timestamp = entry["DateTime"]
        entry_datetime = None
        count=count+1 
        entry_datetime = datetime.strptime(entry_timestamp, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=timezone.utc)
        
        distance = abs((entry_datetime - target_datetime).total_seconds())
        if distance < closest_distance:
            closest_distance = distance
            closest_location = entry

    distanceInMinutes = closest_distance / 60
    if closest_location:
        return closest_location["Latitude"], closest_location["Longitude"], distanceInMinutes
    else:
        return None, None, None
