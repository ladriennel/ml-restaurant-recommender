from fastapi.responses import JSONResponse
import os
import requests
import time
import math
from typing import List, Dict, Set
from dotenv import load_dotenv
from threading import Lock

load_dotenv()

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
TOMTOM_BASE_URL = "https://api.tomtom.com/search/2/poiDetails"

cache: Dict[str, List[Dict]] = {}
last_request_time = 0
MIN_REQUEST_INTERVAL = 1
request_lock = Lock()