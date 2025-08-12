import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import logging
import json
import re
from dataclasses import dataclass
from sqlalchemy.orm import Session
from models import Restaurant as RestaurantModel, CityRestaurant as CityRestaurantModel

logger = logging.getLogger(__name__)

# ML Model Configuration Constants
SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2'
SENTENCE_EMBEDDING_DIM = 384  

# Feature Processing Constants
PRICE_SCALE_MIN = 1
PRICE_SCALE_MAX = 5
SEMANTIC_EMBEDDING_WEIGHT = 0.5  # Weight for semantic vs exact matching
SIMILARITY_THRESHOLD = 0.5  # Threshold for matched features
COSINE_SIM_NORMALIZATION_OFFSET = 1  # To convert [-1,1] to [0,1]
NEUTRAL_SIMILARITY_SCORE = 0.5  # Default when data is missing

@dataclass
class RestaurantFeatures:
    """Structured features for a restaurant"""
    restaurant_id: int
    name: str
    cuisine: str
    price_level: Optional[int]
    description: str
    review_summary: str
    menu_highlights: List[str]
    tags: List[str]
    
    # Processed features
    cuisine_vector: np.ndarray = None
    price_score: float = None
    description_embeddings: np.ndarray = None
    review_embeddings: np.ndarray = None
    menu_embeddings: np.ndarray = None
    tags_embeddings: np.ndarray = None
    combined_score: float = 0.0

@dataclass
class RecommendationResult:
    """Single recommendation result"""
    restaurant_id: int
    restaurant_name: str
    address: str
    tomtom_poi_id: str
    similarity_score: float
    feature_scores: Dict[str, float]

class RestaurantRecommendationSystem:
    """Main recommendation system using multiple ML techniques"""
    
    def __init__(self):
        # Load pre-trained models
        self.sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
        
        # For feature scaling when combining different score types
        self.scaler = StandardScaler()
        
        # Feature weights (rebalanced for semantic embeddings)
        self.feature_weights = {
            'cuisine': 0.18,      
            'price': 0.15,        
            'description': 0.20,   
            'review': 0.12,       
            'menu': 0.20,        
            'tags': 0.15
        }
        
        logger.info("Restaurant recommendation system initialized for Groq data")

    def extract_features_from_restaurants(
        self, 
        restaurants: List[RestaurantModel], 
        restaurant_type: str = "user"
    ) -> List[RestaurantFeatures]:
        """Extract and process features from restaurant objects"""
        
        features_list = []
        
        for restaurant in restaurants:
            try:
                # Get details or use empty defaults
                details = restaurant.details if restaurant.details else None
                
                # Parse JSON fields safely
                menu_highlights = []
                tags = []
                
                if details and details.menu_highlights:
                    try:
                        menu_highlights = json.loads(details.menu_highlights)
                    except (json.JSONDecodeError, TypeError):
                        menu_highlights = []
                
                if details and details.tags:
                    try:
                        tags = json.loads(details.tags)
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                
                features = RestaurantFeatures(
                    restaurant_id=restaurant.id,
                    name=restaurant.name,
                    cuisine=details.cuisine if details else "",
                    price_level=details.price_level if details else None,
                    description=details.description if details else "",
                    review_summary=details.review_summary if details else "",
                    menu_highlights=menu_highlights,
                    tags=tags
                )
                
                features_list.append(features)
                
            except Exception as e:
                logger.error(f"Error extracting features from {restaurant.name}: {e}")
                # Add minimal features to avoid breaking the system
                features_list.append(RestaurantFeatures(
                    restaurant_id=restaurant.id,
                    name=restaurant.name,
                    cuisine="",
                    price_level=None,
                    description="",
                    review_summary="",
                    menu_highlights=[],
                    tags=[]
                ))
        
        logger.info(f"Extracted features from {len(features_list)} {restaurant_type} restaurants")
        return features_list

    def process_cuisine_features(self, features_list: List[RestaurantFeatures]) -> None:
        """Process cuisine using direct semantic embeddings of Groq data"""
        
        logger.info("Processing cuisine features with semantic embeddings")
        
        # Collect all cuisine texts
        cuisine_texts = []
        for features in features_list:
            # Use Groq cuisine directly, add context if empty
            cuisine_text = features.cuisine if features.cuisine else "restaurant"
            cuisine_texts.append(cuisine_text)
        
        try:
            # Generate embeddings for all cuisines at once (more efficient)
            cuisine_embeddings = self.sentence_model.encode(
                cuisine_texts,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Assign embeddings to features
            for i, features in enumerate(features_list):
                features.cuisine_vector = cuisine_embeddings[i]
                
        except Exception as e:
            logger.error(f"Error generating cuisine embeddings: {e}")
            # Fallback to zeros
            for features in features_list:
                features.cuisine_vector = np.zeros(SENTENCE_EMBEDDING_DIM)

    def process_price_features(self, features_list: List[RestaurantFeatures]) -> None:
        """Process price level using proximity scoring"""
        
        logger.info("Processing price level features")
        
        for features in features_list:
            # Normalize price level to 0-1 scale
            if features.price_level is not None:
                features.price_score = (features.price_level - PRICE_SCALE_MIN) / (PRICE_SCALE_MAX - PRICE_SCALE_MIN)
            else:
                features.price_score = NEUTRAL_SIMILARITY_SCORE  

    def process_text_features(self, features_list: List[RestaurantFeatures]) -> None:
        """Process description and review summary separately using sentence embeddings"""
        
        logger.info("Processing description and review features with sentence transformers")
        
        # Prepare separate description and review texts
        description_texts = []
        review_texts = []
        
        for features in features_list:
            # Description text
            desc_text = features.description.strip() if features.description.strip() else f"{features.name} restaurant"
            description_texts.append(desc_text)
            
            # Review text  
            review_text = features.review_summary.strip() if features.review_summary.strip() else "customer reviews"
            review_texts.append(review_text)
        
        try:
            # Generate embeddings for descriptions
            description_embeddings = self.sentence_model.encode(
                description_texts,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Generate embeddings for reviews
            review_embeddings = self.sentence_model.encode(
                review_texts,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Assign embeddings to features
            for i, features in enumerate(features_list):
                features.description_embeddings = description_embeddings[i]
                features.review_embeddings = review_embeddings[i]
                
        except Exception as e:
            logger.error(f"Error generating text embeddings: {e}")
            # Fallback to zeros
            for features in features_list:
                features.description_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)
                features.review_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)

    def process_menu_and_tags_features(self, features_list: List[RestaurantFeatures]) -> None:
        """Process menu highlights and tags using individual item embeddings for better semantic accuracy"""
        
        logger.info("Processing menu highlights and tags with individual item embeddings")
        
        try:
            # Process each restaurant's menu and tags individually
            for features in features_list:
                # Process menu highlights - embed each item separately
                menu_items = features.menu_highlights or []
                if menu_items:
                    # Clean menu items
                    clean_menu_items = [str(item).strip().strip('"') for item in menu_items if item and str(item).strip()]
                    if clean_menu_items:
                        # Generate embeddings for each menu item
                        menu_embeddings = self.sentence_model.encode(
                            clean_menu_items,
                            convert_to_tensor=False,
                            show_progress_bar=False
                        )
                        # Average all menu item embeddings to represent the restaurant's menu
                        features.menu_embeddings = np.mean(menu_embeddings, axis=0)
                    else:
                        features.menu_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)
                else:
                    features.menu_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)
                
                # Process tags - embed each tag separately
                tag_items = features.tags or []
                if tag_items:
                    # Clean tag items
                    clean_tag_items = [str(tag).strip().strip('"') for tag in tag_items if tag and str(tag).strip()]
                    if clean_tag_items:
                        # Generate embeddings for each tag
                        tag_embeddings = self.sentence_model.encode(
                            clean_tag_items,
                            convert_to_tensor=False,
                            show_progress_bar=False
                        )
                        # Average all tag embeddings to represent the restaurant's characteristics
                        features.tags_embeddings = np.mean(tag_embeddings, axis=0)
                    else:
                        features.tags_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)
                else:
                    features.tags_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)
                
                logger.debug(f"{features.name}: menu_items={len(features.menu_highlights)}, tags={len(features.tags)}, menu_dim={len(features.menu_embeddings)}, tags_dim={len(features.tags_embeddings)}")
                
        except Exception as e:
            logger.error(f"Error processing menu/tags: {e}")
            # Fallback to zero vectors
            for features in features_list:
                features.menu_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)
                features.tags_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)

    def calculate_feature_similarities(
        self, 
        user_features: List[RestaurantFeatures], 
        city_features: List[RestaurantFeatures]
    ) -> np.ndarray:
        """Calculate similarity matrix with proper scaling for different feature types"""
        
        logger.info(f"Calculating similarities: {len(user_features)} user vs {len(city_features)} city restaurants")
        
        similarity_matrix = np.zeros((len(city_features), len(user_features)))
        feature_details = {}
        
        for i, city_restaurant in enumerate(city_features):
            city_scores = []
            
            for j, user_restaurant in enumerate(user_features):
                scores = {}
                
                # 1. Cuisine similarity (semantic embeddings)
                if (city_restaurant.cuisine_vector is not None and 
                    user_restaurant.cuisine_vector is not None):
                    cuisine_sim = cosine_similarity(
                        [city_restaurant.cuisine_vector], 
                        [user_restaurant.cuisine_vector]
                    )[0][0]
                    # Convert from [-1, 1] to [0, 1]
                    cuisine_sim = (cuisine_sim + COSINE_SIM_NORMALIZATION_OFFSET) / 2
                else:
                    cuisine_sim = NEUTRAL_SIMILARITY_SCORE  
                scores['cuisine'] = cuisine_sim
                
                # 2. Price proximity (unchanged)
                if (city_restaurant.price_score is not None and 
                    user_restaurant.price_score is not None):
                    price_diff = abs(city_restaurant.price_score - user_restaurant.price_score)
                    price_sim = max(0, 1.0 - price_diff)
                else:
                    price_sim = NEUTRAL_SIMILARITY_SCORE 
                scores['price'] = price_sim
                
                # 3. Description similarity (semantic embeddings)
                if (city_restaurant.description_embeddings is not None and 
                    user_restaurant.description_embeddings is not None):
                    desc_sim = cosine_similarity(
                        [city_restaurant.description_embeddings], 
                        [user_restaurant.description_embeddings]
                    )[0][0]
                    desc_sim = (desc_sim + COSINE_SIM_NORMALIZATION_OFFSET) / 2
                else:
                    desc_sim = NEUTRAL_SIMILARITY_SCORE
                scores['description'] = desc_sim
                
                # 4. Review similarity (semantic embeddings)
                if (city_restaurant.review_embeddings is not None and 
                    user_restaurant.review_embeddings is not None):
                    review_sim = cosine_similarity(
                        [city_restaurant.review_embeddings], 
                        [user_restaurant.review_embeddings]
                    )[0][0]
                    review_sim = (review_sim + COSINE_SIM_NORMALIZATION_OFFSET) / 2
                else:
                    review_sim = NEUTRAL_SIMILARITY_SCORE
                scores['review'] = review_sim
                
                # 5. Menu similarity (semantic embeddings)
                if (city_restaurant.menu_embeddings is not None and 
                    user_restaurant.menu_embeddings is not None):
                    menu_sim = cosine_similarity(
                        [city_restaurant.menu_embeddings], 
                        [user_restaurant.menu_embeddings]
                    )[0][0]
                    # Convert from [-1, 1] to [0, 1]
                    menu_sim = (menu_sim + COSINE_SIM_NORMALIZATION_OFFSET) / 2
                else:
                    menu_sim = NEUTRAL_SIMILARITY_SCORE
                scores['menu'] = menu_sim
                
                # 6. Tags similarity (semantic embeddings)
                if (city_restaurant.tags_embeddings is not None and 
                    user_restaurant.tags_embeddings is not None):
                    tags_sim = cosine_similarity(
                        [city_restaurant.tags_embeddings], 
                        [user_restaurant.tags_embeddings]
                    )[0][0]
                    # Convert from [-1, 1] to [0, 1]
                    tags_sim = (tags_sim + COSINE_SIM_NORMALIZATION_OFFSET) / 2
                else:
                    tags_sim = NEUTRAL_SIMILARITY_SCORE
                scores['tags'] = tags_sim
                
                # Calculate weighted similarity using all 6 features
                weighted_sim = (
                    scores['cuisine'] * self.feature_weights['cuisine'] +
                    scores['price'] * self.feature_weights['price'] +
                    scores['description'] * self.feature_weights['description'] +
                    scores['review'] * self.feature_weights['review'] +
                    scores['menu'] * self.feature_weights['menu'] +
                    scores['tags'] * self.feature_weights['tags']
                )
                
                similarity_matrix[i][j] = weighted_sim
                city_scores.append((scores, weighted_sim))
            
            # Store best match details for this city restaurant
            best_match_idx = np.argmax(similarity_matrix[i])
            feature_details[i] = city_scores[best_match_idx][0]
        
        return similarity_matrix, feature_details

    def get_recommendations(
        self,
        user_restaurants: List[RestaurantModel],
        city_restaurants: List[CityRestaurantModel],
        top_k: int = 10
    ) -> List[RecommendationResult]:
        """Generate top-k restaurant recommendations"""
        
        logger.info(f"Generating recommendations: {len(user_restaurants)} user restaurants, {len(city_restaurants)} city restaurants")
        
        # Extract features
        user_features = self.extract_features_from_restaurants(user_restaurants, "user")
        city_features = self.extract_features_from_restaurants(city_restaurants, "city")
        
        if not user_features or not city_features:
            logger.warning("No features extracted, returning empty recommendations")
            return []
        
        # Process all feature types
        all_features = user_features + city_features
        self.process_cuisine_features(all_features)
        self.process_price_features(all_features)
        self.process_text_features(all_features)
        self.process_menu_and_tags_features(all_features)
        
        # Calculate similarities
        similarity_matrix, feature_details = self.calculate_feature_similarities(user_features, city_features)
        
        # Get best overall similarity for each city restaurant
        city_restaurant_scores = []
        for i, city_restaurant in enumerate(city_restaurants):
            # Take maximum similarity across all user restaurants
            max_similarity = np.max(similarity_matrix[i])
            best_user_match = np.argmax(similarity_matrix[i])
            
            # Get feature breakdown
            feature_scores = feature_details[i]
            
            city_restaurant_scores.append({
                'restaurant': city_restaurant,
                'similarity': max_similarity,
                'feature_scores': feature_scores,
                'best_user_match': user_restaurants[best_user_match].name
            })
        
        # Filter out restaurants with same names as user restaurants
        user_restaurant_names = set()
        for user_restaurant in user_restaurants:
            normalized_name = user_restaurant.name.lower().strip()
            user_restaurant_names.add(normalized_name)
        
        # Filter city restaurants with different names
        filtered_city_scores = []
        seen_names = set()  
        
        for score_data in city_restaurant_scores:
            city_name = score_data['restaurant'].name.lower().strip()
            
            # Skip if matches user restaurant or already seen
            if city_name not in user_restaurant_names and city_name not in seen_names:
                filtered_city_scores.append(score_data)
                seen_names.add(city_name)
        
        logger.info(f"Filtered out {len(city_restaurant_scores) - len(filtered_city_scores)} duplicate restaurants")
        
        # Sort by similarity and take top k from filtered results
        filtered_city_scores.sort(key=lambda x: x['similarity'], reverse=True)
        top_recommendations = filtered_city_scores[:top_k]
        
        # Convert to RecommendationResult objects
        recommendations = []
        for rec in top_recommendations:
            restaurant = rec['restaurant']
            recommendations.append(RecommendationResult(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                address=restaurant.address,
                tomtom_poi_id=restaurant.tomtom_poi_id or "",
                similarity_score=rec['similarity'],
                feature_scores=rec['feature_scores']
            ))
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

# Global instance
recommendation_system = RestaurantRecommendationSystem()