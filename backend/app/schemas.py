from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Position(BaseModel):
    lat: float
    lon: float

class RestaurantDetailsBase(BaseModel):
    tomtom_poi_id: str
    description: Optional[str] = ""
    review_summary: Optional[str] = ""
    menu_highlights: List[str] = []  # Parse JSON to list in response
    price_level: Optional[int] = None
    cuisine: Optional[str] = ""
    tags: List[str] = []  # Parse JSON to list in response

class RestaurantDetailsResponse(RestaurantDetailsBase):
    id: int
    groq_processed: bool = False
    groq_model_used: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RestaurantBase(BaseModel):
    name: str
    address: str
    categories: List[str] = []
    categorySet: List[int] = []
    position: Optional[Position] = None
    tomtom_poi_id: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):  
    id: int
    search_id: int
    details: Optional[RestaurantDetailsResponse] = None
    
    class Config:
        from_attributes = True

class Restaurant(RestaurantBase):
    id: int
    search_id: int
    details: Optional[RestaurantDetailsResponse] = None
    
    class Config:
        from_attributes = True

class CityRestaurantBase(BaseModel):
    name: str
    address: str
    categories: List[str] = []
    categorySet: List[int] = []
    position: Optional[Position] = None
    tomtom_poi_id: Optional[str] = None

class CityRestaurantCreate(CityRestaurantBase):
    pass

class CityRestaurant(CityRestaurantBase):
    id: int
    search_id: int
    details: Optional[RestaurantDetailsResponse] = None
    
    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    population: Optional[int] = None

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    pass

class SearchBase(BaseModel):
    location: Optional[Location] = None
    restaurants: List[Optional[RestaurantCreate]] = []

class SearchCreate(SearchBase):
    pass

class CityRestaurantResponse(BaseModel):
    name: str
    address: str
    categories: List[str] = []
    categorySet: List[int] = []
    position: Optional[Position] = None
    tomtom_poi_id: Optional[str] = None
    details: Optional[RestaurantDetailsResponse] = None

class SearchResponse(BaseModel):
    id: int
    location: Optional[Location] = None
    restaurants: List[RestaurantResponse] = []
    city_restaurants: List[CityRestaurantResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True