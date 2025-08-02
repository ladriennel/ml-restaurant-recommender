from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Set
from database import get_db
from models import Search, Restaurant as RestaurantModel, CityRestaurant as CityRestaurantModel
from schemas import SearchCreate, SearchResponse
from city_restaurant import search_city_restaurants
import json

router = APIRouter()

@router.post("/searches", response_model=SearchResponse)
async def create_search(search_data: SearchCreate, db: Session = Depends(get_db)):
    """Store a new search with location and selected restaurants"""
    try:
        # Create the search entry
        db_search = Search(
            location_name=search_data.location.name if search_data.location else None,
            location_latitude=search_data.location.latitude if search_data.location else None,
            location_longitude=search_data.location.longitude if search_data.location else None,
            location_population=search_data.location.population if search_data.location else None,
        )
        
        db.add(db_search)
        db.commit()
        db.refresh(db_search)  # Get the ID without committing
        
        # Add restaurants
        for restaurant_data in search_data.restaurants:
            if restaurant_data:  # Skip null restaurants
                db_restaurant = RestaurantModel(
                    search_id=db_search.id,
                    name=restaurant_data.name,
                    address=restaurant_data.address,
                    categories=json.dumps(restaurant_data.categories) if restaurant_data.categories else None,
                    category_set=json.dumps(restaurant_data.categorySet) if restaurant_data.categorySet else None,
                    position_lat=restaurant_data.position.lat if restaurant_data.position else None,
                    position_lon=restaurant_data.position.lon if restaurant_data.position else None,
                )
                db.add(db_restaurant)
        
        db.commit()
        
        if search_data.location:
            await search_and_store_city_restaurants(db_search, search_data, db)
        
        # Get the complete search data to return
        return await get_search(db_search.id, db)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating search: {e}")
        raise HTTPException(status_code=500, detail="Failed to save search data")

async def search_and_store_city_restaurants(db_search: Search, search_data: SearchCreate, db: Session):
    """Search for restaurants in the city and store them"""
    try:
        # Collect unique category IDs from user-selected restaurants
        category_ids: Set[int] = set()
        for restaurant_data in search_data.restaurants:
            if restaurant_data and restaurant_data.categorySet:
                category_ids.update(restaurant_data.categorySet)
        
        if not category_ids:
            category_ids = {7315}  
        
        print(f"Searching city restaurants with categories: {category_ids}")
        
        population = search_data.location.population or 100000  # Default if no population data
        
        # Search for restaurants in the city
        city_restaurants = await search_city_restaurants(
            center_lat=search_data.location.latitude,
            center_lon=search_data.location.longitude,
            category_ids=category_ids,
            population=population,
        )
        
        print(f"Found {len(city_restaurants)} restaurants in city")
        
        # Store city restaurants in database
        for restaurant_data in city_restaurants:
            db_city_restaurant = CityRestaurantModel(
                search_id=db_search.id,
                name=restaurant_data["name"],
                address=restaurant_data["address"],
                categories=json.dumps(restaurant_data.get("categories", [])),
                category_set=json.dumps(restaurant_data.get("categorySet", [])),
                position_lat=restaurant_data.get("position", {}).get("lat") if restaurant_data.get("position") else None,
                position_lon=restaurant_data.get("position", {}).get("lon") if restaurant_data.get("position") else None,
                distance_from_center=restaurant_data.get("distance_from_center"),
                tomtom_poi_id=restaurant_data.get("tomtom_poi_id")
            )
            db.add(db_city_restaurant)
        
        db.commit()
        print(f"Stored {len(city_restaurants)} city restaurants in database")
        
    except Exception as e:
        print(f"Error searching/storing city restaurants: {e}")
        # Don't fail the entire request if city search fails
        db.rollback()

@router.get("/searches/{search_id}", response_model=SearchResponse)
async def get_search(search_id: int, db: Session = Depends(get_db)):
    """Retrieve a search by ID"""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    # Get associated restaurants
    restaurants = db.query(RestaurantModel).filter(RestaurantModel.search_id == search_id).all()
    
    # Get associated city restaurants
    city_restaurants = db.query(CityRestaurantModel).filter(CityRestaurantModel.search_id == search_id).all()

    # Convert to response format
    location = None
    if search.location_name:
        location = {
            "name": search.location_name,
            "latitude": search.location_latitude,
            "longitude": search.location_longitude,
            "population": search.location_population
        }
    
    restaurant_list = []
    for restaurant in restaurants:
        restaurant_dict = {
            "name": restaurant.name,
            "address": restaurant.address,
            "categories": json.loads(restaurant.categories) if restaurant.categories else [],
            "categorySet": json.loads(restaurant.category_set) if restaurant.category_set else [],
        }
        if restaurant.position_lat and restaurant.position_lon:
            restaurant_dict["position"] = {
                "lat": restaurant.position_lat,
                "lon": restaurant.position_lon
            }
        restaurant_list.append(restaurant_dict)

    city_restaurant_list = []
    for city_restaurant in city_restaurants:
        city_restaurant_dict = {
            "name": city_restaurant.name,
            "address": city_restaurant.address,
            "categories": json.loads(city_restaurant.categories) if city_restaurant.categories else [],
            "categorySet": json.loads(city_restaurant.category_set) if city_restaurant.category_set else [],
            "distance_from_center": city_restaurant.distance_from_center,
            "tomtom_poi_id": city_restaurant.tomtom_poi_id
        }
        if city_restaurant.position_lat and city_restaurant.position_lon:
            city_restaurant_dict["position"] = {
                "lat": city_restaurant.position_lat,
                "lon": city_restaurant.position_lon
            }
        city_restaurant_list.append(city_restaurant_dict)

    return SearchResponse(
        id=search.id,
        location=location,
        restaurants=restaurant_list,
        city_restaurants=city_restaurant_list,
        created_at=search.created_at
    )

@router.get("/searches", response_model=List[SearchResponse])
async def get_all_searches(db: Session = Depends(get_db)):
    """Get all searches"""
    searches = db.query(Search).all()
    result = []
    
    for search in searches:
        restaurants = db.query(RestaurantModel).filter(RestaurantModel.search_id == search.id).all()
        city_restaurants = db.query(CityRestaurantModel).filter(CityRestaurantModel.search_id == search.id).all()
        
        location = None
        if search.location_name:
            location = {
                "name": search.location_name,
                "latitude": search.location_latitude,
                "longitude": search.location_longitude,
                "population": search.location_population,
            }
        
        restaurant_list = []
        for restaurant in restaurants:
            restaurant_dict = {
                "name": restaurant.name,
                "address": restaurant.address,
                "categories": json.loads(restaurant.categories) if restaurant.categories else [],
                "categorySet": json.loads(restaurant.category_set) if restaurant.category_set else [],
            }
            if restaurant.position_lat and restaurant.position_lon:
                restaurant_dict["position"] = {
                    "lat": restaurant.position_lat,
                    "lon": restaurant.position_lon
                }
            restaurant_list.append(restaurant_dict)

        # Convert city restaurants
        city_restaurant_list = []
        for city_restaurant in city_restaurants:
            city_restaurant_dict = {
                "name": city_restaurant.name,
                "address": city_restaurant.address,
                "categories": json.loads(city_restaurant.categories) if city_restaurant.categories else [],
                "categorySet": json.loads(city_restaurant.category_set) if city_restaurant.category_set else [],
                "distance_from_center": city_restaurant.distance_from_center,
                "tomtom_poi_id": city_restaurant.tomtom_poi_id
            }
            if city_restaurant.position_lat and city_restaurant.position_lon:
                city_restaurant_dict["position"] = {
                    "lat": city_restaurant.position_lat,
                    "lon": city_restaurant.position_lon
                }
            city_restaurant_list.append(city_restaurant_dict)
        
        result.append(SearchResponse(
            id=search.id,
            location=location,
            restaurants=restaurant_list,
            city_restaurants=city_restaurant_list,
            created_at=search.created_at
        ))
    
    return result