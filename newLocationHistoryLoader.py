import json

def parse_test_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    raw_signals = []
    for signal in data.get('rawSignals', []):
        position = signal.get('position', {})
        lat_lng = position.get('LatLng')
        timestamp = position.get('timestamp')
        if lat_lng and timestamp:
            # Remove the ° character from LatLng
            lat_lng = lat_lng.replace('Â°', '')
            # Split lat_lng into latitude and longitude
            latitude, longitude = lat_lng.split(', ')
            raw_signals.append({
                'latitude': latitude,
                'longitude': longitude,
                'timestamp': timestamp
            })
    
    return {'rawSignals': raw_signals}

# Example usage
file_path = 'C:/Users/rick4/Downloads/New folder (2)/test.json'
parsed_data = parse_test_json(file_path)
print(parsed_data)