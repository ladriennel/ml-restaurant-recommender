from pydantic import BaseModel
from typing import List, Optional

class LocationBase(BaseModel):
    city: str
    region:str
    country: str

class Location(LocationBase):
    id: int
    class Config:
        orm_mode = True

class RestaurantBase(BaseModel):
    name: str
    categories: List[str]
    price: Optional[str]
    rating: float
    url: str
    tags: Optional[List[str]] = []
    review_snippets: Optional[List[str]] = []  # For ML later
    location_id: int

class Restaurant(RestaurantBase):
    id: int
    class Config:
        orm_mode = True
