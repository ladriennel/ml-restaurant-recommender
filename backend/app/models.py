from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Search(Base):
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, nullable=True)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    location_population = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to restaurants
    restaurants = relationship("Restaurant", back_populates="search", cascade="all, delete-orphan")
    # Relationship to city restaurants found in area
    city_restaurants = relationship("CityRestaurant", back_populates="search", cascade="all, delete-orphan")

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    categories = Column(Text, nullable=True) 
    category_set = Column(Text, nullable=True)  
    position_lat = Column(Float, nullable=True)
    position_lon = Column(Float, nullable=True)
    
    # Relationship back to search
    search = relationship("Search", back_populates="restaurants")

class CityRestaurant(Base):
    __tablename__ = "city_restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    categories = Column(Text, nullable=True) 
    category_set = Column(Text, nullable=True) 
    position_lat = Column(Float, nullable=True)
    position_lon = Column(Float, nullable=True)
    distance_from_center = Column(Float, nullable=True)  # Distance in km from city center
    tomtom_poi_id = Column(String, nullable=True)  # TomTom POI ID for future reference
    
    # Relationship back to search
    search = relationship("Search", back_populates="city_restaurants")