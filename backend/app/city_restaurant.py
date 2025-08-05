from fastapi.responses import JSONResponse
import os
import requests
import time
from typing import List, Dict, Set
from dotenv import load_dotenv
from threading import Lock
import logging

logger = logging.getLogger(__name__)

load_dotenv()

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
TOMTOM_BASE_URL = "https://api.tomtom.com/search/2/categorySearch"

cache: Dict[str, List[Dict]] = {}
last_request_time = 0
MIN_REQUEST_INTERVAL = 1
request_lock = Lock()

def calculate_city_radius(population: int) -> int:
    """
    Calculate appropriate search radius based on actual city population.
    Returns radius in meters.
    """
    if population < 10000:
        return 5000  
    elif population < 50000:
        return 10000  
    elif population < 200000:
        return 20000 
    elif population < 1000000:
        return 30000  
    else:
        return 50000  


async def search_city_restaurants(
    center_lat: float,
    center_lon: float,
    category_ids: Set[int],
    population: int,
) -> List[Dict]:
    """
    Search for restaurants in a city using TomTom API.
    Returns:
        List of restaurant dictionaries
    """
    global last_request_time

    all_restaurants = []
    seen_restaurants = set()  
    radius = calculate_city_radius(population)
    
    if not category_ids:
        category_ids = {7315} 

    category_set_str = ",".join(map(str, category_ids))
    cache_key = f"{center_lat},{center_lon},{category_set_str},{radius}"

    if cache_key in cache:
        logger.info(f"Returning cached results for city restaurants")
        return cache[cache_key]
    
    try:
        with request_lock:
            current_time = time.time()
            elapsed = current_time - last_request_time
            
            if elapsed < MIN_REQUEST_INTERVAL:
                time.sleep(MIN_REQUEST_INTERVAL - elapsed)

            url = f"{TOMTOM_BASE_URL}/.json"
            params = {
                "key": TOMTOM_API_KEY,
                "lat": center_lat,
                "lon": center_lon,
                "radius": radius,
                "limit": 100,  # TomTom max is 100 per request
                "language": "en-US",
                "categorySet": category_set_str
            }
            
            response = requests.get(url, params=params, timeout=15)
            last_request_time = time.time()
            
            if response.status_code == 429:
                logger.warning("Rate limited for city restaurant search")
                # Return empty list instead of JSONResponse
                return []

            if response.status_code != 200:
                logger.error(f"TomTom API error for city search: {response.status_code}")
                # Return empty list instead of JSONResponse
                return []
            
            data = response.json()
            
            for result in data.get("results", []):
                poi = result.get("poi", {})
                address = result.get("address", {})
                position = result.get("position", {})
                
                # Create unique identifier to avoid duplicates
                restaurant_key = f"{poi.get('name', '')}-{address.get('freeformAddress', '')}"
                
                if restaurant_key in seen_restaurants:
                    continue
                
                seen_restaurants.add(restaurant_key)
                
                restaurant_data = {
                    "name": poi.get("name", "Unknown Restaurant"),
                    "categories": poi.get("categories", []),
                    "categorySet": [cat.get("id") for cat in poi.get("categorySet", [])],
                    "address": address.get("freeformAddress", "Unknown location"),
                    "tomtom_poi_id": result.get("id")
                }
                
                if position:
                    restaurant_lat = position.get("lat")
                    restaurant_lon = position.get("lon")
                    restaurant_data["position"] = {
                        "lat": restaurant_lat,
                        "lon": restaurant_lon
                    }
                
                all_restaurants.append(restaurant_data)
        
    except requests.exceptions.Timeout:
        logger.error("Timeout error in city restaurant search")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in city restaurant search: {e}")
        return []
    
    
    cache[cache_key] = all_restaurants

    logger.info(f"Found {len(all_restaurants)} unique restaurants in city")
    return all_restaurants