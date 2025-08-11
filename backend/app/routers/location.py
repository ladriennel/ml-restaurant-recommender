from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict
import time
from threading import Lock
import logging

logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()

GEODB_API_HOST = "wft-geo-db.p.rapidapi.com"
GEODB_API_KEY = os.getenv("GEODB_API_KEY") 

cache = {}
last_request_time = 0
MIN_REQUEST_INTERVAL = 1.2
request_lock = Lock()

@router.get("/locations")
async def search_locations(query: str = Query(..., min_length=1)) -> List[Dict]:

    global last_request_time
    
    # Check cache first
    if query in cache:
        return cache[query]
    
    with request_lock: 
        current_time = time.time()
        elapsed = current_time - last_request_time

        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)

        url = f"https://{GEODB_API_HOST}/v1/geo/cities"
        headers = {
            "X-RapidAPI-Key": GEODB_API_KEY,
            "X-RapidAPI-Host": GEODB_API_HOST,
        }
        params = {
            "namePrefix": query,
            "types": "CITY",
            "minPopulation":1000,
            "sort": "-population",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            last_request_time = time.time()

            if response.status_code == 429:
                logger.warning(f"Rate limited for query: {query}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded. Please slow down your typing."}
                )

            if response.status_code != 200:
                logger.error(f"GeoDB API error: {response.status_code}, {response.text}")
                return JSONResponse(status_code=500, content={"error": "GeoDB API failure"})

            data = response.json()
            results = []
            for city in data.get("data", []):
                city_name = city.get('city', 'Unknown City')
                region = city.get('region', city.get('regionCode', ''))
                country = city.get('countryCode', city.get('country', ''))
                
                # Skip cities with numbers in the name
                if any(char.isdigit() for char in city_name):
                    continue
                
                if region:
                    formatted_city = f"{city_name}, {region}, {country}"
                else:
                    formatted_city = f"{city_name}, {country}"
                    
                results.append({
                    "name": formatted_city,
                    "latitude": city.get("latitude"),
                    "longitude": city.get("longitude"),
                    "population": city.get('population', 0),
                })
            cache[query] = results
            return results

        except requests.exceptions.Timeout:
            return JSONResponse(status_code=500, content={"error": "API timeout"})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JSONResponse(status_code=500, content={"error": "Internal server error"})
