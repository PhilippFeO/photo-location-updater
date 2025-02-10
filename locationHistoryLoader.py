import json
from datetime import datetime, timezone
import re

def parse_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    timeline_objects = data.get("timelineObjects", [])
    extracted_data = []

    for obj in timeline_objects:
        if "activitySegment" in obj:
            activity_segment = obj["activitySegment"]
            start_location = activity_segment.get("startLocation", {})
            start_timestamp = activity_segment.get("duration", {}).get("startTimestamp", "")
            
            if start_location and start_timestamp:
                latitude = start_location.get("latitudeE7", 0) / 1e7
                longitude = start_location.get("longitudeE7", 0) / 1e7
                extracted_data.append({
                    "DateTime": start_timestamp,
                    "Latitude": latitude,
                    "Longitude": longitude
                })

    return extracted_data

"""
Google changed the location history to be stored in the mobile device only.
with this change they also changed the format of the location history json file.
"""
def parse_json_file_v2(file_path):
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



def get_closest_location(data, target_timestamp):
    closest_location = None
    closest_distance = float("inf")
    distance = 0
    for entry in data:
        entry_timestamp = entry["DateTime"]
        entry_datetime = None
        # for some reason google have two different timestamp formats
        timestamp_format_A = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
        timestamp_format_B = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$')
        
        if timestamp_format_A.match(entry_timestamp):            
            entry_datetime = datetime.strptime(entry_timestamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        elif timestamp_format_B.match(entry_timestamp):
            entry_datetime = datetime.strptime(entry_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        else:
            print(f"Invalid timestamp format: {entry_timestamp}")
            continue
        target_datetime = datetime.strptime(target_timestamp, '%Y:%m:%d %H:%M:%S').replace(tzinfo=timezone.utc)
        distance = abs((entry_datetime - target_datetime).total_seconds())
        if distance < closest_distance:
            closest_distance = distance
            closest_location = entry

    distanceInMinutes = closest_distance / 60
    if closest_location:
        return closest_location["Latitude"], closest_location["Longitude"], distanceInMinutes
    else:
        return None, None, None

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

if __name__ == "__main__":
    file_path = "2024_AUGUST.json"
    data = parse_json_file(file_path)
    for entry in data:
        print(entry)