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

class RestaurantCreate(RestaurantBase):
    pass

class Restaurant(RestaurantBase):
    id: int
    search_id: int
    
    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    name: str
    latitude: float
    longitude: float

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    pass

class SearchBase(BaseModel):
    location: Optional[Location] = None
    restaurants: List[Optional[RestaurantCreate]] = []

class SearchCreate(SearchBase):
    pass

class SearchResponse(BaseModel):
    id: int
    location: Optional[Location] = None
    restaurants: List[Optional[RestaurantCreate]] = []
    created_at: datetime
    
    class Config:
        from_attributes = True