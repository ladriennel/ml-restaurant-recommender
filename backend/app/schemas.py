from pydantic import BaseModel

class LocationBase(BaseModel):
    name: str
    country: str

class Location(LocationBase):
    id: int
    class Config:
        orm_mode = True

class RestaurantBase(BaseModel):
    name: str
    cuisine: str
    price: str
    location_id: int

class Restaurant(RestaurantBase):
    id: int
    class Config:
        orm_mode = True
