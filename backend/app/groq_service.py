import os
import json
import asyncio
import aiohttp
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from threading import Lock
import time

logger = logging.getLogger(__name__)

@dataclass
class GroqResponse:
    description: str = ""
    review_summary: str = ""
    menu_highlights: List[str] = None
    price_level: Optional[int] = None
    cuisine: str = ""
    tags: List[str] = None
    model_used: str = ""
    success: bool = False

# Global state for rate limiting and caching 
cache: Dict[str, GroqResponse] = {}
last_request_time = 0
MIN_REQUEST_INTERVAL = 0.6   
request_lock = Lock()

# Rate limit tracking
request_timestamps_primary = []
request_timestamps_fallback = []
daily_request_count_primary = 0
daily_request_count_fallback = 0
daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

PRIMARY_MODEL = "moonshotai/kimi-k2-instruct"

RATE_LIMITS = {
    PRIMARY_MODEL: {
        "requests_per_minute": 55,  
        "requests_per_day": 1000    
    }
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY environment variable is required")

def _check_rate_limits(model: str) -> bool:
    """Check if we can make a request without hitting rate limits"""
    global daily_request_count_primary, daily_request_count_fallback, daily_reset_time
    
    now = datetime.now()
    
    # Reset daily counter if it's a new day
    if now >= daily_reset_time + timedelta(days=1):
        daily_request_count_primary = 0
        daily_request_count_fallback = 0
        daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get appropriate tracking variables
    if model == PRIMARY_MODEL:
        timestamps = request_timestamps_primary
        daily_count = daily_request_count_primary
    else:
        timestamps = request_timestamps_fallback
        daily_count = daily_request_count_fallback
    
    limits = RATE_LIMITS[model]
    
    # Check daily limit
    if daily_count >= limits["requests_per_day"]:
        logger.warning(f"Daily request limit reached for {model}")
        return False
    
    with request_lock:
        # Clean old timestamps (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        timestamps[:] = [ts for ts in timestamps if ts > cutoff]
        
        # Check per-minute limit
        if len(timestamps) >= limits["requests_per_minute"]:
            logger.warning(f"Per-minute rate limit reached for {model}")
            return False
        
        return True

def _record_request(model: str):
    """Record a successful request for rate limiting"""
    global daily_request_count_primary, daily_request_count_fallback
    
    with request_lock:
        if model == PRIMARY_MODEL:
            request_timestamps_primary.append(datetime.now())
            daily_request_count_primary += 1
        else:
            request_timestamps_fallback.append(datetime.now())
            daily_request_count_fallback += 1

def _create_prompt(restaurant_name: str, restaurant_address: str, categories: List[str] = None) -> str:
    """Create the prompt for Groq API with clear category information"""
    category_info = ""
    if categories:
        # Filter out any non-string categories and create readable list
        category_names = [str(cat) for cat in categories if cat]
        if category_names:
            category_info = f"\nRestaurant Type/Categories: {', '.join(category_names)}"
    
    prompt = f"""You are an API that extracts structured data about a restaurant based on its name, address, and type. Return the information in strict JSON format using the exact schema below. If any data is not available or cannot be reasonably inferred, return empty values ("" for strings, [] for arrays, null for integers).

        Schema:
        {{
        "description": string (brief description of the restaurant, 1-2 sentences),
        "review_summary": string (general customer sentiment and highlights),
        "menu_highlights": string[] (popular or signature dishes/items),
        "price": integer (1 to 5 scale: 1=very cheap, 2=cheap, 3=moderate, 4=expensive, 5=very expensive),
        "cuisine": string (type of cuisine or food category),
        "tags": string[] (descriptive tags like "family-friendly", "romantic", "casual", "upscale", etc.)
        }}

        Restaurant Information:
        Name: {restaurant_name}
        Address: {restaurant_address} {category_info}

        Return only the JSON object with no additional text or commentary."""
            
    return prompt

async def _make_request(prompt: str, model: str) -> Optional[Dict]:
    """Make a request to Groq API"""
    global last_request_time
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "response_format": {"type": "json_object"}
    }
    
    try:
        # Rate limiting similar to restaurant.py style
        with request_lock:
            current_time = time.time()
            elapsed = current_time - last_request_time
            
            if elapsed < MIN_REQUEST_INTERVAL:
                await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GROQ_BASE_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                last_request_time = time.time()
                
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    logger.warning(f"Rate limit hit for model {model}")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status} for model {model}: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error(f"Timeout for model {model}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for model {model}: {e}")
        return None

def _parse_response(response_data: Dict, model_used: str) -> GroqResponse:
    """Parse Groq API response into GroqResponse object"""
    try:
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed_data = json.loads(content)
        
        return GroqResponse(
            description=parsed_data.get("description", ""),
            review_summary=parsed_data.get("review_summary", ""),
            menu_highlights=parsed_data.get("menu_highlights", []),
            price_level=parsed_data.get("price"), 
            cuisine=parsed_data.get("cuisine", ""),
            tags=parsed_data.get("tags", []),
            model_used=model_used,
            success=True
        )
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Failed to parse response from {model_used}: {e}")
        logger.error(f"Raw content that failed to parse: {content}")
        return GroqResponse(model_used=model_used, success=False)

async def get_restaurant_details(restaurant_name: str, restaurant_address: str, tomtom_poi_id: str, categories: List[str] = None) -> GroqResponse:
    """Get enhanced restaurant details from Groq API with Moonshot retry logic"""
    
    # Use tomtom_poi_id as cache key
    cache_key = tomtom_poi_id or f"{restaurant_name}-{restaurant_address}"
    
    # Check cache first
    if cache_key in cache:
        logger.info(f"Returning cached Groq results for {restaurant_name}")
        return cache[cache_key]
    
    prompt = _create_prompt(restaurant_name, restaurant_address, categories)
    
    # Check rate limits for primary model (Moonshot)
    if not _check_rate_limits(PRIMARY_MODEL):
        logger.warning(f"Moonshot rate limit exceeded for {restaurant_name}, skipping Groq processing")
        result = GroqResponse(success=False)
        cache[cache_key] = result
        return result
    
    # Try Moonshot model (first attempt)
    response_data = await _make_request(prompt, PRIMARY_MODEL)
    if response_data:
        _record_request(PRIMARY_MODEL)
        result = _parse_response(response_data, PRIMARY_MODEL)
        cache[cache_key] = result
        return result
    
    # If first attempt failed, wait briefly and retry Moonshot once
    logger.info(f"Moonshot failed for {restaurant_name}, retrying after brief delay")
    await asyncio.sleep(2)  # Brief delay for API recovery
    
    # Check rate limits again before retry
    if not _check_rate_limits(PRIMARY_MODEL):
        logger.warning(f"Moonshot rate limit hit during retry for {restaurant_name}")
        result = GroqResponse(success=False)
        cache[cache_key] = result
        return result
    
    # Retry Moonshot
    response_data = await _make_request(prompt, PRIMARY_MODEL)
    if response_data:
        _record_request(PRIMARY_MODEL)
        result = _parse_response(response_data, PRIMARY_MODEL)
        cache[cache_key] = result
        return result
    
    # Both attempts failed - return empty details rather than poor quality fallback
    logger.warning(f"Moonshot failed twice for {restaurant_name}, creating empty details")
    result = GroqResponse(success=False)
    cache[cache_key] = result
    return result