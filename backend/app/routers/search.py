from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Search, Restaurant as RestaurantModel
from schemas import SearchCreate, SearchResponse
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
        
        return SearchResponse(
            id=db_search.id,
            location=search_data.location,
            restaurants=search_data.restaurants,
            created_at=db_search.created_at
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error creating search: {e}")
        raise HTTPException(status_code=500, detail="Failed to save search data")

@router.get("/searches/{search_id}", response_model=SearchResponse)
async def get_search(search_id: int, db: Session = Depends(get_db)):
    """Retrieve a search by ID"""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    # Get associated restaurants
    restaurants = db.query(RestaurantModel).filter(RestaurantModel.search_id == search_id).all()
    
    # Convert to response format
    location = None
    if search.location_name:
        location = {
            "name": search.location_name,
            "latitude": search.location_latitude,
            "longitude": search.location_longitude
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
    
    return SearchResponse(
        id=search.id,
        location=location,
        restaurants=restaurant_list,
        created_at=search.created_at
    )

@router.get("/searches", response_model=List[SearchResponse])
async def get_all_searches(db: Session = Depends(get_db)):
    """Get all searches"""
    searches = db.query(Search).all()
    result = []
    
    for search in searches:
        restaurants = db.query(RestaurantModel).filter(RestaurantModel.search_id == search.id).all()
        
        location = None
        if search.location_name:
            location = {
                "name": search.location_name,
                "latitude": search.location_latitude,
                "longitude": search.location_longitude
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
        
        result.append(SearchResponse(
            id=search.id,
            location=location,
            restaurants=restaurant_list,
            created_at=search.created_at
        ))
    
    return result