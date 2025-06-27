import requests
from geopy.distance import geodesic
import math
import json

# Load dynamic red zones from JSON file
def load_red_zones(filename="red_zones.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return []

# Get flights near departure coordinates
def get_flights_near_location(min_lat, max_lat, min_lon, max_lon):
    url = f"https://opensky-network.org/api/states/all?lamin={min_lat}&lamax={max_lat}&lomin={min_lon}&lomax={max_lon}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("states", [])
    else:
        return []

# Calculate compass bearing between two coordinates
def calculate_bearing(start, end):
    lat1, lon1 = map(math.radians, start)
    lat2, lon2 = map(math.radians, end)
    d_lon = lon2 - lon1
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

# Check if flight heading is toward destination
def is_heading_toward(flight, dest_coords):
    if not flight[6] or not flight[5] or not flight[10]:
        return False
    current_coords = (flight[6], flight[5])
    target_bearing = calculate_bearing(current_coords, dest_coords)
    return abs(target_bearing - flight[10]) < 45

# Check if coordinates fall within a red zone
def is_in_red_zone(lat, lon, red_zones):
    for zone in red_zones:
        if zone["coordinates"]:
            distance = geodesic((lat, lon), tuple(zone["coordinates"])).km
            if distance <= zone["radius_km"]:
                return zone["alert"]
    return None

# Main function to check risks
def find_flight_risks(dep_coords, dest_coords):
    red_zones = load_red_zones()
    lat, lon = dep_coords
    flights = get_flights_near_location(lat-1, lat+1, lon-1, lon+1)

    results = []

    for flight in flights:
        try:
            if is_heading_toward(flight, dest_coords):
                lat, lon = flight[6], flight[5]
                zone = is_in_red_zone(lat, lon, red_zones)
                results.append({
                    "callsign": flight[1].strip() if flight[1] else "N/A",
                    "origin_country": flight[2],
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": flight[7],
                    "velocity_kmph": round(flight[9] * 3.6, 2) if flight[9] else "N/A",  # m/s to km/h
                    "risk_zone": zone or "None"
                })
        except:
            continue

    return results
