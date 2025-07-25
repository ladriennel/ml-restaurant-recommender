from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    region = Column(String)
    country = Column(String)
    restaurants = relationship("Restaurant", back_populates="location")

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    categories = Column(JSON) 
    price = Column(String)
    rating = Column(Float) 
    review_count = Column(Integer) 
    url = Column(String) 
    tags = Column(JSON)  
    review_snippets = Column(JSON) 
    location_id = Column(Integer, ForeignKey("locations.id"))
    location = relationship("Location", back_populates="restaurants")