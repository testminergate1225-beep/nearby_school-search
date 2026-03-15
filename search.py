

import googlemaps
import json
import time
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Parse command-line arguments first
if len(sys.argv) > 2:
    address = sys.argv[1]
    radius = sys.argv[2]
else:
    print(json.dumps({"error": "Address and radius must be provided as command-line arguments."}))
    exit(1)

# Initialize Google Maps API client
gmaps = googlemaps.Client(key='put_your_api_key')


# --- GRID SEARCH LOGIC TO BYPASS 60-SCHOOL CAP ---
import math
import threading

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

geocode_result = gmaps.geocode(address)
if not geocode_result:
    print(json.dumps({"error": "Could not geocode the address."}))
    exit(1)
user_location = geocode_result[0]['geometry']['location']
center_lat = user_location['lat']
center_lng = user_location['lng']

radius_m = int(radius)
step = int(radius_m * 0.8)  # overlap to avoid missing schools at edges
num_steps = max(1, math.ceil((radius_m * 2) / step))

# Calculate grid points (lat/lng offsets)
def offset_lat(lat, meters):
    return lat + (meters / 111320)
def offset_lng(lat, lng, meters):
    return lng + (meters / (40075000 * math.cos(math.radians(lat)) / 360))

grid_points = []
for i in range(-num_steps//2, num_steps//2 + 1):
    for j in range(-num_steps//2, num_steps//2 + 1):
        lat = offset_lat(center_lat, i * step)
        lng = offset_lng(center_lat, center_lng, j * step)
        grid_points.append((lat, lng))

schools_dict = {}
schools_lock = threading.Lock()

def enrich_school(school):
    # Fetch website using Place Details API if place_id is available
    if school['place_id']:
        try:
            details = gmaps.place(place_id=school['place_id'], fields=['website'])
            website = details.get('result', {}).get('website')
            if website:
                school['website'] = website
                # Try to guess Facebook page from website
                if 'facebook.com' in website:
                    school['facebook'] = website
                else:
                    try:
                        import requests
                        from bs4 import BeautifulSoup
                        resp = requests.get(website, timeout=5)
                        if resp.ok:
                            soup = BeautifulSoup(resp.text, 'html.parser')
                            fb_link = soup.find('a', href=lambda x: x and 'facebook.com' in x)
                            if fb_link:
                                school['facebook'] = fb_link['href']
                    except Exception:
                        pass
        except Exception:
            pass
    return school

def fetch_grid_cell(lat, lng):
    local_schools = []
    next_page_token = None
    while True:
        try:
            if next_page_token:
                time.sleep(2)
                search_results = gmaps.places_nearby(
                    location={"lat": lat, "lng": lng},
                    radius=radius_m,
                    type='school',
                    page_token=next_page_token
                )
            else:
                search_results = gmaps.places_nearby(
                    location={"lat": lat, "lng": lng},
                    radius=radius_m,
                    type='school'
                )
        except Exception as e:
            break
        for place in search_results.get('results', []):
            school = {
                'name': place.get('name', 'N/A'),
                'latitude': place['geometry']['location']['lat'],
                'longitude': place['geometry']['location']['lng'],
                'rating': place.get('rating', None),
                'user_ratings_total': place.get('user_ratings_total', None),
                'address': place.get('vicinity', 'N/A'),
                'place_id': place.get('place_id', None)
            }
            local_schools.append(school)
        next_page_token = search_results.get('next_page_token')
        if not next_page_token:
            break
    # Deduplicate by place_id (thread-safe)
    with schools_lock:
        for s in local_schools:
            if s['place_id'] and s['place_id'] not in schools_dict:
                schools_dict[s['place_id']] = s

# Run grid search in parallel
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(fetch_grid_cell, lat, lng) for lat, lng in grid_points]
    for future in as_completed(futures):
        pass  # just wait for all to finish

# Enrich all unique schools in parallel
schools = list(schools_dict.values())
with ThreadPoolExecutor(max_workers=10) as executor:
    enriched = list(executor.map(enrich_school, schools))
schools = enriched

# Use address and radius from command-line arguments
geocode_result = gmaps.geocode(address)
if not geocode_result:
    print(json.dumps({"error": "Could not geocode the address."}))
    exit(1)
user_location = geocode_result[0]['geometry']['location']
# Output the list of schools in JSON format
json_output = json.dumps(schools, indent=2, ensure_ascii=False)
# print(json_output)  # Uncomment this line to print the JSON output to the console

# Write to schools.json file
with open('schools.json', 'w', encoding='utf-8') as f:
    f.write(json_output)
