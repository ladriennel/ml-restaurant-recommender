from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import location, restaurant, search, ml_routes
import logging

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],  # In dev only, use env origin in prod (origins)
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location.router, prefix="/api", tags=["locations"])
app.include_router(restaurant.router, prefix="/api", tags=["restaurants"])
app.include_router(search.router, prefix="/api", tags=["searches"])
app.include_router(ml_routes.router, prefix="/api", tags=["ml"])


@app.get("/")
async def root():
    return {"message": "TastePoint is running"}

