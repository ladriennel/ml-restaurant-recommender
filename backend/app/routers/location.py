from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv
from typing import List
import time
import asyncio
from threading import Lock

load_dotenv()

router = APIRouter()

GEODB_API_HOST = "wft-geo-db.p.rapidapi.com"
GEODB_API_KEY = os.getenv("GEODB_API_KEY") 

cache = {}
last_request_time = 0
MIN_REQUEST_INTERVAL = 1.2
request_lock = Lock()

@router.get("/locations")
async def search_locations(query: str = Query(..., min_length=1)) -> List[str]:

    global last_request_time
    
    # Check cache first
    if query in cache:
        return cache[query]
    
    async with asyncio.Lock():  # FastAPI async lock for concurrency safety
        current_time = time.time()
        time_since_last_request = current_time - last_request_time

        if time_since_last_request < MIN_REQUEST_INTERVAL:
            await asyncio.sleep(MIN_REQUEST_INTERVAL - time_since_last_request)

        url = f"https://{GEODB_API_HOST}/v1/geo/cities"
        headers = {
            "X-RapidAPI-Key": GEODB_API_KEY,
            "X-RapidAPI-Host": GEODB_API_HOST,
        }
        params = {
            "namePrefix": query,
            "types": "CITY",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            last_request_time = time.time()

            if response.status_code == 429:
                print(f"Rate limited for query: {query}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded. Please slow down your typing."}
                )

            if response.status_code != 200:
                print(f"GeoDB API error: {response.status_code}, {response.text}")
                return JSONResponse(status_code=500, content={"error": "GeoDB API failure"})

            data = response.json()
            results = [
                f"{city['city']}, {city['region']}, {city['countryCode']}"
                for city in data.get("data", [])
            ]
            cache[query] = results
            return results

        except requests.exceptions.Timeout:
            return JSONResponse(status_code=500, content={"error": "API timeout"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JSONResponse(status_code=500, content={"error": "Internal server error"})
