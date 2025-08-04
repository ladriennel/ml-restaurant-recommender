from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Position(BaseModel):
    lat: float
    lon: float

class RestaurantBase(BaseModel):
    name: str
    address: str
    categories: List[str] = []
    categorySet: List[int] = []
    position: Optional[Position] = None
    tomtom_poi_id: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class Restaurant(RestaurantBase):
    id: int
    search_id: int
    
    class Config:
        from_attributes = True

class CityRestaurantBase(BaseModel):
    name: str
    address: str
    categories: List[str] = []
    categorySet: List[int] = []
    position: Optional[Position] = None
    distance_from_center: Optional[float] = None
    tomtom_poi_id: Optional[str] = None

class CityRestaurantCreate(CityRestaurantBase):
    pass

class CityRestaurant(CityRestaurantBase):
    id: int
    search_id: int
    
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
    distance_from_center: Optional[float] = None
    tomtom_poi_id: Optional[str] = None

class SearchResponse(BaseModel):
    id: int
    location: Optional[Location] = None
    restaurants: List[Optional[RestaurantCreate]] = []
    city_restaurants: List[CityRestaurantResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True