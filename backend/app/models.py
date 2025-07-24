from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    country = Column(String)

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cuisine = Column(String)
    price = Column(String)
    location_id = Column(Integer, ForeignKey("locations.id"))
