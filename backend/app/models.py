from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RestaurantDetails(Base):
    """Shared table for enhanced restaurant information from Groq API"""
    __tablename__ = "restaurant_details"
    
    id = Column(Integer, primary_key=True, index=True)

    tomtom_poi_id = Column(String, unique=True, nullable=False, index=True)
    
    # Groq-enhanced data
    description = Column(Text, nullable=True)
    review_summary = Column(Text, nullable=True)
    menu_highlights = Column(Text, nullable=True)  # JSON array as string
    price_level = Column(Integer, nullable=True)  # 1-5 scale
    cuisine = Column(String, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array as string
    
    # Metadata
    groq_processed = Column(Boolean, default=False)
    groq_model_used = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Search(Base):
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, nullable=True)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    location_population = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    restaurants = relationship("Restaurant", back_populates="search", cascade="all, delete-orphan")
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
    tomtom_poi_id = Column(String, nullable=True)
    
    details_id = Column(Integer, ForeignKey("restaurant_details.id"), nullable=True)

    # Relationships
    search = relationship("Search", back_populates="restaurants")
    details = relationship("RestaurantDetails")

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
    tomtom_poi_id = Column(String, nullable=True)  # TomTom POI ID for future reference
    
    details_id = Column(Integer, ForeignKey("restaurant_details.id"), nullable=True)
    
    # Relationships
    search = relationship("Search", back_populates="city_restaurants")
    details = relationship("RestaurantDetails")