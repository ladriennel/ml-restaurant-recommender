from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import os
import requests
from dotenv import load_dotenv
import time
from typing import List, Dict
from threading import Lock

load_dotenv()

router = APIRouter()

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
TOMTOM_BASE_URL = "https://api.tomtom.com/search/2/search"

cache: Dict[str, List[Dict]] = {}
last_request_time = 0
MIN_REQUEST_INTERVAL = 1
request_lock = Lock()

@router.get("/restaurants/search")
async def search_restaurants(query: str = Query(..., min_length=1)) -> List[Dict]:

    global last_request_time

    # Check cache
    if query in cache:
        return cache[query]

    with request_lock:
        current_time = time.time()
        elapsed = current_time - last_request_time

        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)

        url = f"{TOMTOM_BASE_URL}/{query}.json"
        params = {
            "key": TOMTOM_API_KEY,
            "limit": 10,
            "language":"en-US",
            "typeahead": True,
            "categorySet": "7315",  
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            last_request_time = time.time()

            if response.status_code == 429:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded. Please slow down your typing."}
                )

            if response.status_code != 200:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"TomTom API error: {response.status_code}"}
                )

            data = response.json()
            
            results = []
            for result in data.get("results", []):
                poi = result.get("poi", {})
                address = result.get("address", {})
                position = result.get("position", {})
               
                restaurant = {
                    "name": poi.get("name", "Unknown Restaurant"),
                    "categories": poi.get("categories", []),
                    "categorySet": [cat.get("id") for cat in poi.get("categorySet", [])],
                    "address": address.get("freeformAddress", "Unknown location"),
                    "tomtom_poi_id": result.get("id")
                }

                if position:
                    restaurant["position"] = {
                        "lat": position.get("lat"),
                        "lon": position.get("lon")
                }
                
                results.append(restaurant)

            cache[query] = results
            return results

        except requests.exceptions.Timeout:
            return JSONResponse(status_code=500, content={"error": "API timeout"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JSONResponse(status_code=500, content={"error": "Internal server error"})
