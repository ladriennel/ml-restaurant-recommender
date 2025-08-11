from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Set
from database import get_db
from models import Search, Restaurant as RestaurantModel, CityRestaurant as CityRestaurantModel, RestaurantDetails
from schemas import SearchCreate, SearchResponse, RestaurantResponse, CityRestaurantResponse, RestaurantDetailsResponse
from city_restaurant import search_city_restaurants
from groq_service import get_restaurant_details
import json
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Semaphore to control concurrent Groq requests 
GROQ_SEMAPHORE = asyncio.Semaphore(20) 

async def process_all_restaurants(
    user_restaurants_data: List[dict], 
    city_restaurants_data: List[dict],
    search_id: int, 
    db: Session
):
    """Simplified restaurant processing with timeout and better error handling"""
    
    total_restaurants = len(user_restaurants_data) + len(city_restaurants_data)
    logger.info(f"Processing {total_restaurants} restaurants with timeouts")
    
    # Process restaurants sequentially to avoid deadlocks
    successful_count = 0
    failed_count = 0
    
    # Process user restaurants
    for restaurant_data in user_restaurants_data:
        try:
            details_id = None
            
            # Try to get Groq details with timeout
            if restaurant_data.get("tomtom_poi_id"):
                try:
                    # Add timeout wrapper
                    details_id = await asyncio.wait_for(
                        get_or_create_restaurant_details(
                            restaurant_data["name"],
                            restaurant_data["address"],
                            restaurant_data.get("tomtom_poi_id"),
                            restaurant_data.get("categories", []),
                            db
                        ),
                        timeout=30.0  # 30 second timeout per restaurant
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout getting details for {restaurant_data['name']}")
                    details_id = None
                except Exception as e:
                    logger.error(f"Error getting details for {restaurant_data['name']}: {e}")
                    details_id = None
            
            # Insert restaurant record
            db_restaurant = RestaurantModel(
                search_id=search_id,
                name=restaurant_data["name"],
                address=restaurant_data["address"],
                categories=json.dumps(restaurant_data.get("categories", [])),
                category_set=json.dumps(restaurant_data.get("categorySet", [])),
                position_lat=restaurant_data.get("position", {}).get("lat") if restaurant_data.get("position") else None,
                position_lon=restaurant_data.get("position", {}).get("lon") if restaurant_data.get("position") else None,
                tomtom_poi_id=restaurant_data.get("tomtom_poi_id"),
                details_id=details_id
            )
            db.add(db_restaurant)
            db.commit()
            successful_count += 1
            logger.info(f"Successfully processed user restaurant: {restaurant_data['name']}")
            
        except Exception as e:
            logger.error(f"Failed to process user restaurant {restaurant_data['name']}: {e}")
            db.rollback()
            failed_count += 1
    
    # Process city restaurants  
    for restaurant_data in city_restaurants_data:
        try:
            details_id = None
            
            # Try to get Groq details with timeout
            if restaurant_data.get("tomtom_poi_id"):
                try:
                    details_id = await asyncio.wait_for(
                        get_or_create_restaurant_details(
                            restaurant_data["name"],
                            restaurant_data["address"],
                            restaurant_data.get("tomtom_poi_id"),
                            restaurant_data.get("categories", []),
                            db
                        ),
                        timeout=30.0  # 30 second timeout per restaurant
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout getting details for {restaurant_data['name']}")
                    details_id = None
                except Exception as e:
                    logger.error(f"Error getting details for {restaurant_data['name']}: {e}")
                    details_id = None
            
            # Insert restaurant record
            db_restaurant = CityRestaurantModel(
                search_id=search_id,
                name=restaurant_data["name"],
                address=restaurant_data["address"],
                categories=json.dumps(restaurant_data.get("categories", [])),
                category_set=json.dumps(restaurant_data.get("categorySet", [])),
                position_lat=restaurant_data.get("position", {}).get("lat") if restaurant_data.get("position") else None,
                position_lon=restaurant_data.get("position", {}).get("lon") if restaurant_data.get("position") else None,
                tomtom_poi_id=restaurant_data.get("tomtom_poi_id"),
                details_id=details_id
            )
            db.add(db_restaurant)
            db.commit()
            successful_count += 1
            logger.info(f"Successfully processed city restaurant: {restaurant_data['name']}")
            
        except Exception as e:
            logger.error(f"Failed to process city restaurant {restaurant_data['name']}: {e}")
            db.rollback()
            failed_count += 1
    
    logger.info(f"Restaurant processing complete: {successful_count} successful, {failed_count} failed")

async def get_or_create_restaurant_details(
    name: str, 
    address: str, 
    tomtom_poi_id: str,
    categories: List[str], 
    db: Session
) -> int:
    """Get existing or create new restaurant details using Groq API"""
    
    if not tomtom_poi_id:
        logger.warning(f"No tomtom_poi_id for restaurant: {name}")
        return None
    
    try:
        # Check if details already exist
        existing_details = db.query(RestaurantDetails).filter(
            RestaurantDetails.tomtom_poi_id == tomtom_poi_id
        ).first()
        
        if existing_details:
            logger.info(f"Using existing details for {name}")
            return existing_details.id
        
        async with GROQ_SEMAPHORE:
            try:
                groq_response = await get_restaurant_details(name, address, tomtom_poi_id, categories)
                
                # Ensure proper data types for JSON storage
                menu_highlights_json = json.dumps(groq_response.menu_highlights or [])
                tags_json = json.dumps(groq_response.tags or [])
                
                restaurant_details = RestaurantDetails(
                    tomtom_poi_id=tomtom_poi_id,
                    description=groq_response.description or "",
                    review_summary=groq_response.review_summary or "",
                    menu_highlights=menu_highlights_json,  # Store as JSON string
                    price_level=groq_response.price_level,  # Integer or None
                    cuisine=groq_response.cuisine or "",
                    tags=tags_json,  # Store as JSON string
                    groq_processed=groq_response.success,
                    groq_model_used=groq_response.model_used if groq_response.success else None
                )
                
                db.add(restaurant_details)
                db.commit()
                db.refresh(restaurant_details)
                
                logger.info(f"Created restaurant details for {name} using {'Groq' if groq_response.success else 'fallback'}")
                return restaurant_details.id
                
            except Exception as e:
                logger.error(f"Failed to create restaurant details for {name}: {e}")
                db.rollback()
                
                # Create fallback empty record
                try:
                    restaurant_details = RestaurantDetails(
                        tomtom_poi_id=tomtom_poi_id,
                        description="",
                        review_summary="",
                        menu_highlights="[]",  # Empty JSON array
                        price_level=None,
                        cuisine="",
                        tags="[]",  # Empty JSON array
                        groq_processed=False
                    )
                    db.add(restaurant_details)
                    db.commit()
                    db.refresh(restaurant_details)
                    return restaurant_details.id
                except Exception as fallback_error:
                    logger.error(f"Failed to create fallback details for {name}: {fallback_error}")
                    db.rollback()
                    return None
                
    except Exception as e:
        logger.error(f"Database error for restaurant {name}: {e}")
        db.rollback()
        return None

def convert_restaurant_details_to_response(details: RestaurantDetails) -> RestaurantDetailsResponse:
    """Convert database RestaurantDetails to response format with proper JSON parsing"""
    if not details:
        return None
    
    try:
        # Parse JSON strings back to lists, with fallback to empty lists
        menu_highlights = []
        if details.menu_highlights:
            try:
                menu_highlights = json.loads(details.menu_highlights)
            except (json.JSONDecodeError, TypeError):
                menu_highlights = []
        
        tags = []
        if details.tags:
            try:
                tags = json.loads(details.tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        
        return RestaurantDetailsResponse(
            id=details.id,
            tomtom_poi_id=details.tomtom_poi_id,
            description=details.description or "",
            review_summary=details.review_summary or "",
            menu_highlights=menu_highlights,  # List[str]
            price_level=details.price_level,  # int or None
            cuisine=details.cuisine or "",
            tags=tags,  # List[str]
            groq_processed=details.groq_processed,
            groq_model_used=details.groq_model_used,
            created_at=details.created_at,
            updated_at=details.updated_at
        )
    except Exception as e:
        logger.error(f"Error converting restaurant details: {e}")
        # Return minimal response on error
        return RestaurantDetailsResponse(
            id=details.id,
            tomtom_poi_id=details.tomtom_poi_id,
            description="",
            review_summary="",
            menu_highlights=[],
            price_level=None,
            cuisine="",
            tags=[],
            groq_processed=False,
            groq_model_used=None,
            created_at=details.created_at,
            updated_at=details.updated_at
        )

def convert_restaurant_to_response(restaurant: RestaurantModel) -> RestaurantResponse:
    """Convert database Restaurant to response format"""
    try:
        # Parse JSON fields with fallback
        categories = []
        if restaurant.categories:
            try:
                categories = json.loads(restaurant.categories)
            except (json.JSONDecodeError, TypeError):
                categories = []
        
        category_set = []
        if restaurant.category_set:
            try:
                category_set = json.loads(restaurant.category_set)
            except (json.JSONDecodeError, TypeError):
                category_set = []
        
        # Convert position
        position = None
        if restaurant.position_lat is not None and restaurant.position_lon is not None:
            position = {
                "lat": restaurant.position_lat,
                "lon": restaurant.position_lon
            }
        
        # Convert details
        details = convert_restaurant_details_to_response(restaurant.details) if restaurant.details else None
        
        return RestaurantResponse(
            id=restaurant.id,
            search_id=restaurant.search_id,
            name=restaurant.name,
            address=restaurant.address,
            categories=categories,  # List[str]
            categorySet=category_set,  # List[int]
            position=position,
            tomtom_poi_id=restaurant.tomtom_poi_id,
            details=details
        )
    except Exception as e:
        logger.error(f"Error converting restaurant {restaurant.name}: {e}")
        # Return minimal response on error
        return RestaurantResponse(
            id=restaurant.id,
            search_id=restaurant.search_id,
            name=restaurant.name,
            address=restaurant.address,
            categories=[],
            categorySet=[],
            position=None,
            tomtom_poi_id=restaurant.tomtom_poi_id,
            details=None
        )

def convert_city_restaurant_to_response(city_restaurant: CityRestaurantModel) -> CityRestaurantResponse:
    """Convert database CityRestaurant to response format"""
    try:
        # Parse JSON fields with fallback
        categories = []
        if city_restaurant.categories:
            try:
                categories = json.loads(city_restaurant.categories)
            except (json.JSONDecodeError, TypeError):
                categories = []
        
        category_set = []
        if city_restaurant.category_set:
            try:
                category_set = json.loads(city_restaurant.category_set)
            except (json.JSONDecodeError, TypeError):
                category_set = []
        
        # Convert position
        position = None
        if city_restaurant.position_lat is not None and city_restaurant.position_lon is not None:
            position = {
                "lat": city_restaurant.position_lat,
                "lon": city_restaurant.position_lon
            }
        
        # Convert details
        details = convert_restaurant_details_to_response(city_restaurant.details) if city_restaurant.details else None
        
        return CityRestaurantResponse(
            id=city_restaurant.id,
            search_id=city_restaurant.search_id,
            name=city_restaurant.name,
            address=city_restaurant.address,
            categories=categories,  # List[str]
            categorySet=category_set,  # List[int]
            position=position,
            tomtom_poi_id=city_restaurant.tomtom_poi_id,
            details=details
        )
    except Exception as e:
        logger.error(f"Error converting city restaurant {city_restaurant.name}: {e}")
        # Return minimal response on error
        return CityRestaurantResponse(
            id=city_restaurant.id,
            search_id=city_restaurant.search_id,
            name=city_restaurant.name,
            address=city_restaurant.address,
            categories=[],
            categorySet=[],
            position=None,
            tomtom_poi_id=city_restaurant.tomtom_poi_id,
            details=None
        )

@router.post("/searches", response_model=SearchResponse)
async def create_search(search_data: SearchCreate, db: Session = Depends(get_db)):
    """Store a new search with location and selected restaurants"""
    try:
        logger.info("=== STARTING CREATE SEARCH ===")
        # Create the search entry
        db_search = Search(
            location_name=search_data.location.name if search_data.location else None,
            location_latitude=search_data.location.latitude if search_data.location else None,
            location_longitude=search_data.location.longitude if search_data.location else None,
            location_population=search_data.location.population if search_data.location else None,
        )
        
        db.add(db_search)
        db.commit()
        db.refresh(db_search) 
        logger.info(f"Created search with ID: {db_search.id}")
        
        # Prepare user restaurant data
        user_restaurants_data = []
        for restaurant_data in search_data.restaurants:
            if restaurant_data:  # Skip null restaurants
                user_restaurants_data.append({
                    "name": restaurant_data.name,
                    "address": restaurant_data.address,
                    "categories": restaurant_data.categories,
                    "categorySet": restaurant_data.categorySet,
                    "position": restaurant_data.position.dict() if restaurant_data.position else None,
                    "tomtom_poi_id": restaurant_data.tomtom_poi_id
                })

        # Get city restaurants 
        city_restaurants_data = []
        if search_data.location:
            logger.info("=== STARTING CITY RESTAURANT SEARCH ===")
            category_ids: Set[int] = set()
            for restaurant_data in search_data.restaurants:
                if restaurant_data and restaurant_data.categorySet:
                    category_ids.update(restaurant_data.categorySet)
            
            if not category_ids:
                category_ids = {7315}  
            
            logger.info(f"Searching city restaurants with categories: {category_ids}")
            
            population = search_data.location.population or 40000
            
            city_restaurants_data = await search_city_restaurants(
                center_lat=search_data.location.latitude,
                center_lon=search_data.location.longitude,
                city_name=search_data.location.name,  
                category_ids=category_ids,
                population=population,
            )
            
            logger.info(f"Found {len(city_restaurants_data)} city restaurants")
            logger.info("=== COMPLETED CITY RESTAURANT SEARCH ===")
        
        logger.info("=== STARTING CONCURRENT GROQ PROCESSING ===")
        await process_all_restaurants(
            user_restaurants_data, 
            city_restaurants_data,
            db_search.id, 
            db
        )

        result = await get_search(db_search.id, db)
        logger.info(f"Search {db_search.id} completed successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error creating search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create search: {str(e)}")

@router.get("/searches/{search_id}", response_model=SearchResponse)
async def get_search(search_id: int, db: Session = Depends(get_db)):
    """Retrieve a search by ID with proper data type conversion"""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    # Get restaurants with details using joinedload for efficiency
    restaurants = db.query(RestaurantModel).options(
        joinedload(RestaurantModel.details)
    ).filter(RestaurantModel.search_id == search_id).all()
    
    city_restaurants = db.query(CityRestaurantModel).options(
        joinedload(CityRestaurantModel.details)
    ).filter(CityRestaurantModel.search_id == search_id).all()

    # Convert to response format with proper data types
    location = None
    if search.location_name:
        location = {
            "name": search.location_name,
            "latitude": search.location_latitude,
            "longitude": search.location_longitude,
            "population": search.location_population
        }
    
    # Convert restaurants to proper response format
    restaurant_list = [convert_restaurant_to_response(restaurant) for restaurant in restaurants]
    city_restaurant_list = [convert_city_restaurant_to_response(city_restaurant) for city_restaurant in city_restaurants]

    return SearchResponse(
        id=search.id,
        location=location,
        restaurants=restaurant_list,  # List[RestaurantResponse]
        city_restaurants=city_restaurant_list,  # List[CityRestaurantResponse]
        created_at=search.created_at
    )

@router.get("/searches", response_model=List[SearchResponse])
async def get_all_searches(db: Session = Depends(get_db)):
    """Get all searches with proper data type conversion"""
    searches = db.query(Search).all()
    result = []
    
    for search in searches:
        restaurants = db.query(RestaurantModel).options(
            joinedload(RestaurantModel.details)
        ).filter(RestaurantModel.search_id == search.id).all()
        
        city_restaurants = db.query(CityRestaurantModel).options(
            joinedload(CityRestaurantModel.details)
        ).filter(CityRestaurantModel.search_id == search.id).all()
        
        location = None
        if search.location_name:
            location = {
                "name": search.location_name,
                "latitude": search.location_latitude,
                "longitude": search.location_longitude,
                "population": search.location_population,
            }
        
        # Convert to proper response format
        restaurant_list = [convert_restaurant_to_response(restaurant) for restaurant in restaurants]
        city_restaurant_list = [convert_city_restaurant_to_response(city_restaurant) for city_restaurant in city_restaurants]
        
        result.append(SearchResponse(
            id=search.id,
            location=location,
            restaurants=restaurant_list,
            city_restaurants=city_restaurant_list,
            created_at=search.created_at
        ))
    
    return result