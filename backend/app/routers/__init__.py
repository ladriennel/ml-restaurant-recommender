from .location import router as location_router
from .restaurant import router as restaurant_router
from .search import router as search_router

__all__ = ["location_router", "restaurant_router", "search_router"]