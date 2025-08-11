from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from models import Restaurant as RestaurantModel, CityRestaurant as CityRestaurantModel
from ml_recommendations import recommendation_system, RecommendationResult
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    restaurant_id: int
    restaurant_name: str
    address: str
    tomtom_poi_id: str
    similarity_score: float
    feature_scores: dict
    explanation: str

class RecommendationRequest(BaseModel):
    """Request model for recommendations"""
    search_id: int
    top_k: Optional[int] = 10

@router.post("/recommendations", response_model=List[RecommendationResponse])
async def get_restaurant_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get ML-powered restaurant recommendations based on user preferences"""
    
    try:
        logger.info(f"Getting recommendations for search_id: {request.search_id}")
        
        # Get user-selected restaurants with details
        user_restaurants = db.query(RestaurantModel).options(
            joinedload(RestaurantModel.details)
        ).filter(RestaurantModel.search_id == request.search_id).all()
        
        if not user_restaurants:
            raise HTTPException(
                status_code=404, 
                detail=f"No user restaurants found for search_id {request.search_id}"
            )
        
        # Get city restaurants with details
        city_restaurants = db.query(CityRestaurantModel).options(
            joinedload(CityRestaurantModel.details)
        ).filter(CityRestaurantModel.search_id == request.search_id).all()
        
        if not city_restaurants:
            raise HTTPException(
                status_code=404, 
                detail=f"No city restaurants found for search_id {request.search_id}"
            )
        
        logger.info(f"Found {len(user_restaurants)} user restaurants and {len(city_restaurants)} city restaurants")
        
        # Generate recommendations using ML system
        recommendations = recommendation_system.get_recommendations(
            user_restaurants=user_restaurants,
            city_restaurants=city_restaurants,
            top_k=request.top_k
        )
        
        if not recommendations:
            logger.warning("No recommendations generated")
            return []
        
        # Convert to response format with explanations
        response_recommendations = []
        for i, rec in enumerate(recommendations):
            # Generate explanation
            explanation = generate_explanation(rec, i + 1)
            
            response_recommendations.append(RecommendationResponse(
                restaurant_id=rec.restaurant_id,
                restaurant_name=rec.restaurant_name,
                address=rec.address,
                tomtom_poi_id=rec.tomtom_poi_id,
                similarity_score=round(rec.similarity_score, 3),
                feature_scores={k: round(v, 3) for k, v in rec.feature_scores.items()},
                explanation=explanation
            ))
        
        logger.info(f"Returning {len(response_recommendations)} recommendations")
        return response_recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate recommendations: {str(e)}"
        )

def generate_explanation(rec: RecommendationResult, rank: int) -> str:
    """Generate human-readable explanation for recommendation"""
    
    explanations = []
    
    # Similarity score explanation
    score_thresholds = [
        (0.8, "Excellent match"),
        (0.7, "Very good match"),
        (0.5, "Good match"),
        (0.0, "Moderate match")
    ]
    
    for threshold, description in score_thresholds:
        if rec.similarity_score > threshold:
            explanations.append(description)
            break
    
    # Feature-specific explanations with mapping to avoid duplicates
    feature_mappings = {
        'cuisine': "cuisine",
        'description': "atmosphere and style",
        'tags': "atmosphere and style",
        'menu': "menu offerings"
    }
    
    feature_explanations = set()
    for feature, score in rec.feature_scores.items():
        if score > 0.8 and feature in feature_mappings:
            feature_explanations.add(feature_mappings[feature])
    
    if feature_explanations:
        explanations.append(f"{', '.join(sorted(feature_explanations))}")
    
    return ": similar ".join(explanations)

@router.get("/recommendations/explain/{search_id}")
async def explain_recommendations(
    search_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed explanation of recommendation methodology"""
    
    try:
        # Get basic stats
        user_count = db.query(RestaurantModel).filter(
            RestaurantModel.search_id == search_id
        ).count()
        
        city_count = db.query(CityRestaurantModel).filter(
            CityRestaurantModel.search_id == search_id
        ).count()
        
        explanation = {
            "methodology": {
                "description": "Multi-feature similarity scoring using machine learning",
                "features": {
                    "cuisine": {
                        "method": "One-hot encoding with Jaccard similarity",
                        "weight": recommendation_system.feature_weights['cuisine'],
                        "description": "Matches restaurants with similar cuisine types"
                    },
                    "price": {
                        "method": "Proximity scoring on 1-5 scale",
                        "weight": recommendation_system.feature_weights['price'],
                        "description": "Finds restaurants in similar price ranges"
                    },
                    "description": {
                        "method": "Sentence embeddings + cosine similarity",
                        "weight": recommendation_system.feature_weights['description'],
                        "description": "Analyzes restaurant descriptions and reviews for atmosphere/style"
                    },
                    "menu_tags": {
                        "method": "Semantic embeddings of menu items and tags",
                        "weight": recommendation_system.feature_weights['menu_tags'],
                        "description": "Compares specific dishes and restaurant characteristics"
                    }
                },
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            },
            "data_stats": {
                "user_restaurants": user_count,
                "city_restaurants": city_count,
                "total_comparisons": user_count * city_count
            },
            "scoring": {
                "range": "0.0 to 1.0 (higher is better)",
                "calculation": "Weighted sum of individual feature similarities",
                "ranking": "Top 10 highest scoring city restaurants"
            }
        }
        
        return explanation
        
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanation")

@router.get("/recommendations/debug/{search_id}")
async def debug_recommendations(
    search_id: int,
    restaurant_id: Optional[int] = Query(None, description="Specific restaurant to debug"),
    db: Session = Depends(get_db)
):
    """Debug endpoint to see detailed feature processing"""
    
    try:
        # Get restaurants
        user_restaurants = db.query(RestaurantModel).options(
            joinedload(RestaurantModel.details)
        ).filter(RestaurantModel.search_id == search_id).all()
        
        city_restaurants = db.query(CityRestaurantModel).options(
            joinedload(CityRestaurantModel.details)
        ).filter(CityRestaurantModel.search_id == search_id).all()
        
        # Extract features for debugging
        user_features = recommendation_system.extract_features_from_restaurants(user_restaurants, "user")
        city_features = recommendation_system.extract_features_from_restaurants(city_restaurants, "city")
        
        debug_info = {
            "user_restaurants": [],
            "city_restaurants": [] if restaurant_id is None else None,
            "specific_restaurant": None
        }
        
        # User restaurant features
        for features in user_features:
            debug_info["user_restaurants"].append({
                "id": features.restaurant_id,
                "name": features.name,
                "cuisine": features.cuisine,
                "price_level": features.price_level,
                "description_length": len(features.description),
                "review_length": len(features.review_summary),
                "menu_items": len(features.menu_highlights),
                "tags": len(features.tags),
                "has_groq_data": bool(features.description or features.review_summary)
            })
        
        # City restaurant features (limited for performance)
        if restaurant_id is None:
            # Show summary for all city restaurants
            debug_info["city_restaurants"] = {
                "total_count": len(city_features),
                "with_groq_data": sum(1 for f in city_features if f.description or f.review_summary),
                "sample_restaurants": [
                    {
                        "id": f.restaurant_id,
                        "name": f.name,
                        "cuisine": f.cuisine,
                        "has_groq_data": bool(f.description or f.review_summary)
                    }
                    for f in city_features[:5]  # Show first 5 as sample
                ]
            }
        else:
            # Show specific restaurant details
            specific = next((f for f in city_features if f.restaurant_id == restaurant_id), None)
            if specific:
                debug_info["specific_restaurant"] = {
                    "id": specific.restaurant_id,
                    "name": specific.name,
                    "cuisine": specific.cuisine,
                    "price_level": specific.price_level,
                    "description": specific.description[:200] + "..." if len(specific.description) > 200 else specific.description,
                    "review_summary": specific.review_summary[:200] + "..." if len(specific.review_summary) > 200 else specific.review_summary,
                    "menu_highlights": specific.menu_highlights,
                    "tags": specific.tags
                }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")