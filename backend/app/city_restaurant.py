from fastapi.responses import JSONResponse
import os
import requests
import time
from typing import List, Dict, Set, Optional
from dotenv import load_dotenv
from threading import Lock
import logging

logger = logging.getLogger(__name__)

load_dotenv()

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
TOMTOM_BASE_URL = "https://api.tomtom.com/search/2/categorySearch"

cache: Dict[str, List[Dict]] = {}
bbox_cache: Dict[str, Dict] = {}  
last_request_time = 0
MIN_REQUEST_INTERVAL = 1
request_lock = Lock()
bbox_cache_lock = Lock()

async def get_city_bounding_box(city_name: str, lat: float, lon: float) -> Optional[Dict]:
    """
    Get city bounding box using Nominatim API with smart fallbacks.
    Returns immediately on first successful result.
    Only caches successful results.
    """
    cache_key = f"{city_name}_{lat}_{lon}"
    
    # Check cache first
    with bbox_cache_lock:
        if cache_key in bbox_cache:
            logger.info(f"Using cached bounding box for {city_name}")
            return bbox_cache[cache_key]
    
    try:
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        
        # Parse city name to handle "City, State, Country" format
        city_parts = [part.strip() for part in city_name.split(',')]
        
        # Different search strategies
        search_queries = []
        if len(city_parts) >= 3:
            # "City, State, Country" format
            search_queries.append(city_name)  # Full search first
            search_queries.append(f"{city_parts[0]}, {city_parts[1]}")  # City + Region
            search_queries.append(f"{city_parts[0]}, {city_parts[-1]}")  # City + Country
        elif len(city_parts) == 2:
            # "City, Country" format
            search_queries.append(city_name)  # Full search first
            search_queries.append(city_parts[0])  # Just city name 
        else:
            # Just city name 
            search_queries.append(city_name)
        
        headers = {
            'User-Agent': 'TastePoint/1.0 (restaurant-recommendation-app)'
        }
        
        # Try each query until we get a good result
        for query in search_queries:
            params = {
                'q': query,
                'format': 'json',
                'limit': 5,
                'addressdetails': 1,
                'extratags': 1,
                # Bias search around the provided coordinates 
                'viewbox': f"{lon-0.5},{lat+0.5},{lon+0.5},{lat-0.5}",
                'bounded': 0  # Allow results outside viewbox but prefer inside
            }
            
            logger.info(f"Searching Nominatim for: {query}")
            response = requests.get(nominatim_url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                results = response.json()
                
                for result in results:
                    # Look for city-level results
                    if ('boundingbox' in result and 
                        result.get('type') in ['city', 'town', 'municipality', 'administrative'] and
                        result.get('class') in ['place', 'boundary']):
                        
                        # Check if result is reasonably close to expected coordinates
                        result_lat = float(result.get('lat', 0))
                        result_lon = float(result.get('lon', 0))
                        
                        # Calculate distance from expected location (rough approximation)
                        lat_diff = abs(result_lat - lat)
                        lon_diff = abs(result_lon - lon)
                        max_distance = 0.5  # ~50km tolerance for city center differences
                        
                        if lat_diff > max_distance or lon_diff > max_distance:
                            logger.info(f"Skipping {result.get('display_name')} - too far from expected location ({lat_diff:.3f}, {lon_diff:.3f})")
                            continue
                        
                        bbox = result['boundingbox']  
                        
                        # Validate bounding box size (not too small or too large)
                        lat_diff = float(bbox[1]) - float(bbox[0])  
                        lon_diff = float(bbox[3]) - float(bbox[2]) 
                        
                        if 0.01 <= lat_diff <= 2.0 and 0.01 <= lon_diff <= 2.0:  # Reasonable city size
                            # Verify the bounding box center is also reasonably close to expected coords
                            bbox_center_lat = (float(bbox[0]) + float(bbox[1])) / 2
                            bbox_center_lon = (float(bbox[2]) + float(bbox[3])) / 2
                            bbox_lat_diff = abs(bbox_center_lat - lat)
                            bbox_lon_diff = abs(bbox_center_lon - lon)
                            
                            if bbox_lat_diff > max_distance or bbox_lon_diff > max_distance:
                                logger.info(f"Skipping {result.get('display_name')} - bounding box center too far from expected location")
                                continue
                            
                            # Format for TomTom
                            bbox_result = {
                                'topLeft': f"{bbox[1]},{bbox[2]}",   
                                'btmRight': f"{bbox[0]},{bbox[3]}",  
                                'geobias': f"rectangle:{bbox[1]},{bbox[2]},{bbox[0]},{bbox[3]}",  
                                'source': 'nominatim',
                                'query_used': query,
                                'result_center': f"{result_lat},{result_lon}",
                                'distance_from_expected': f"{lat_diff:.3f},{lon_diff:.3f}",
                                'matched_display_name': result.get('display_name', '')
                            }
                            
                            logger.info(f"Found valid bounding box for {city_name}")
                            logger.info(f"  Query: {query}")
                            logger.info(f"  Matched: {result.get('display_name', '')}")
                            logger.info(f"  Distance from expected: {lat_diff:.3f}°, {lon_diff:.3f}°")
                            logger.info(f"  Geobias: {bbox_result['geobias']}")
                            
                            # Cache only successful results
                            with bbox_cache_lock:
                                bbox_cache[cache_key] = bbox_result
                            return bbox_result
            
            time.sleep(1.1)
        
        logger.warning(f"No suitable bounding box found for {city_name} after trying all queries:")
        for i, query in enumerate(search_queries):
            logger.warning(f"  Query {i+1}: {query}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting bounding box for {city_name}: {e}")
        return None

def generate_fallback_bounding_box(lat: float, lon: float, population: int) -> Dict:
    """
    Generate a reasonable bounding box based on population and location.
    More sophisticated than simple radius.
    """
    # Base size on population
    if population < 50000:
        size = 0.05  # ~5km
    elif population < 200000:
        size = 0.1   # ~10km
    elif population < 1000000:
        size = 0.2   # ~20km
    else:
        size = 0.3   # ~30km
    
    # Adjust for latitude (longitude lines get closer near poles)
    lat_adjustment = 1.0 / max(0.5, abs(lat) / 90.0 + 0.5)
    lon_size = size * lat_adjustment
    
    top_left_lat = lat + size
    top_left_lon = lon - lon_size
    btm_right_lat = lat - size
    btm_right_lon = lon + lon_size
    
    return {
        'topLeft': f"{top_left_lat},{top_left_lon}",
        'btmRight': f"{btm_right_lat},{btm_right_lon}",
        'geobias': f"rectangle:{top_left_lat},{top_left_lon},{btm_right_lat},{btm_right_lon}",
        'source': 'fallback',
        'population_based': True
    }

async def search_city_restaurants(
    center_lat: float,
    center_lon: float,
    city_name: str,  
    category_ids: Set[int],
    population: int,
) -> List[Dict]:
    """
    Search for restaurants in a city using TomTom API with enhanced bounding box support.
    """
    global last_request_time

    all_restaurants = []
    seen_restaurants = set()
    
    if not category_ids:
        category_ids = {7315}
    else:
        category_ids.discard(7315)

    category_set_str = ",".join(map(str, category_ids))
    
    # Try to get bounding box from Nominatim first
    bbox_data = await get_city_bounding_box(city_name, center_lat, center_lon)
    
    if bbox_data and bbox_data.get('source') == 'nominatim':
        # Use Nominatim bounding box
        search_params = {
            "key": TOMTOM_API_KEY,
            "topLeft": bbox_data['topLeft'],
            "btmRight": bbox_data['btmRight'],
            "geobias": bbox_data['geobias'],
            "limit": 100,
            "language": "en-US",
            "categorySet": category_set_str
        }
        logger.info(f"Using Nominatim bounding box for {city_name}")
        
    else:
        # Fallback to population-based bounding box
        bbox_data = generate_fallback_bounding_box(center_lat, center_lon, population)
        
        search_params = {
            "key": TOMTOM_API_KEY,
            "topLeft": bbox_data['topLeft'],
            "btmRight": bbox_data['btmRight'],
            "geobias": bbox_data['geobias'],
            "limit": 100,
            "language": "en-US",
            "categorySet": category_set_str
        }
        logger.info(f"Using fallback bounding box for {city_name}")
    
    # Updated cache key to include bounding box info
    cache_key = f"{center_lat},{center_lon},{city_name},{category_set_str},{bbox_data.get('source')}"

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
            
            response = requests.get(url, params=search_params, timeout=15)
            last_request_time = time.time()
            
            if response.status_code == 429:
                logger.warning("Rate limited for city restaurant search")
                return []

            if response.status_code != 200:
                logger.error(f"TomTom API error for city search: {response.status_code}")
                logger.error(f"Search params: {search_params}")
                return []
            
            data = response.json()
            logger.info(f"TomTom returned {len(data.get('results', []))} results for {city_name}")
            
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
    logger.info(f"Found {len(all_restaurants)} unique restaurants in {city_name} using {bbox_data.get('source', 'unknown')} method")
    return all_restaurants


# Alternative function name to maintain backward compatibility
async def search_city_restaurants_enhanced(
    center_lat: float,
    center_lon: float,
    city_name: str,
    category_ids: Set[int],
    population: int,
) -> List[Dict]:
    """Alias for backward compatibility"""
    return await search_city_restaurants(center_lat, center_lon, city_name, category_ids, population)