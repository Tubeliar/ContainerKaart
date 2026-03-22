import requests
from geopy.distance import geodesic
import heapq
import json
import os
import sys

cache_file = "containers_cache.json"

if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
    print(f"Loading container data from cache: {cache_file}")
    with open(cache_file, "r", encoding="utf-8") as f:
        all_containers = json.load(f)
    print(f"Loaded {len(all_containers)} containers from cache")
else:
    if len(sys.argv) != 3:
        print("Usage: python get_container_locations.py <zipcode> <housenumber>")
        exit(1)
    zipcode, housenumber = sys.argv[1], sys.argv[2]

    # The page that sets the session (postal code + house number determines the area)
    base_url = f"https://www.mijnafvalwijzer.nl/nl/{zipcode}/{housenumber}"
    api_url = "https://www.mijnafvalwijzer.nl/site/containers"

    # Start a session so cookies are carried over (the API needs the session cookie)
    session = requests.Session()

    print(f"Fetching base page to establish session: {base_url}")
    resp = session.get(base_url)
    print(f"Base page status: {resp.status_code}")

    print(f"Fetching container data: {api_url}")
    resp = session.get(api_url)
    print(f"API status: {resp.status_code}")

    all_containers = resp.json().get("containers", [])
    if len(all_containers) == 0:
        print("Error: no containers returned. Not saving cache. Exiting.")
        exit(1)
    print(f"Total containers (all types): {len(all_containers)}")

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_containers, f, ensure_ascii=False, indent=2)
    print(f"Saved to {cache_file}")
target_lat = float(all_containers[0]["initLatitude"])
target_lon = float(all_containers[0]["initLongitude"])

# Filter to restafval only
restafval = [c for c in all_containers if c["WasteType"] == "restafval"]
print(f"Restafval containers: {len(restafval)}")

# Parse coordinates
containers = []
for c in restafval:
    try:
        lat = float(c["latitude"])
        lon = float(c["longitude"])
        containers.append((lat, lon, c))
    except (ValueError, KeyError):
        pass

print(f"Parsed {len(containers)} restafval containers with coordinates")

# Calculate distances and get 15 closest
distances = [
    (geodesic((target_lat, target_lon), (lat, lon)).meters, lat, lon, info)
    for lat, lon, info in containers
]
closest = heapq.nsmallest(15, distances)

# Output results
print(f"\n15 closest restafval containers to ({target_lat}, {target_lon}):")
for dist, lat, lon, info in closest:
    print(f"  {dist:6.0f}m  {lat}, {lon}  —  {info['address']}")
