import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
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

# TF-IDF Configuration Constants
MENU_TFIDF_MAX_FEATURES = 300
MENU_TFIDF_NGRAM_RANGE = (1, 5)
TAGS_TFIDF_MAX_FEATURES = 150
TAGS_TFIDF_NGRAM_RANGE = (1, 3)
TFIDF_MAX_DF = 0.95
TAGS_MAX_DF = 0.9
TFIDF_MIN_DF = 1

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
    text_embeddings: np.ndarray = None
    menu_tags_embeddings: np.ndarray = None
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
    matched_features: List[str]

class RestaurantRecommendationSystem:
    """Main recommendation system using multiple ML techniques"""
    
    def __init__(self):
        # Load pre-trained models
        self.sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
        
        # TF-IDF for menu highlights
        self.menu_tfidf = TfidfVectorizer(
            max_features=MENU_TFIDF_MAX_FEATURES,           
            stop_words='english',
            ngram_range=MENU_TFIDF_NGRAM_RANGE,         
            lowercase=True,
            token_pattern=r'[a-zA-Z-]{2,}', 
            min_df=TFIDF_MIN_DF,                   
            max_df=TFIDF_MAX_DF                
        )
        
        # TF-IDF for tags 
        self.tags_tfidf = TfidfVectorizer(
            max_features=TAGS_TFIDF_MAX_FEATURES,          
            stop_words='english', 
            ngram_range=TAGS_TFIDF_NGRAM_RANGE,         
            lowercase=True,
            token_pattern=r'[a-zA-Z-]{2,}',  
            min_df=TFIDF_MIN_DF,
            max_df=TAGS_MAX_DF                  
        )
        
        # For feature scaling when combining different score types
        self.scaler = StandardScaler()
        
        # Feature weights (adjusted for Groq data quality)
        self.feature_weights = {
            'cuisine': 0.20,       
            'price': 0.20,         
            'description': 0.25,    
            'review': 0.15,         
            'menu_tags': 0.20   
        }
        
        # Track if TF-IDF vectorizers are fitted
        self.menu_tfidf_fitted = False
        self.tags_tfidf_fitted = False
        
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
        """Process description and review summary using sentence embeddings"""
        
        logger.info("Processing text features with sentence transformers")
        
        # Combine description and review for richer context
        combined_texts = []
        for features in features_list:
            text_parts = []
            
            if features.description.strip():
                text_parts.append(features.description.strip())
            if features.review_summary.strip():
                text_parts.append(features.review_summary.strip())
            
            if not text_parts:
                text_parts.append(f"{features.name} {features.cuisine}".strip())
            
            combined_text = " ".join(text_parts)
            combined_texts.append(combined_text)
        
        # Generate embeddings for all texts at once (more efficient)
        try:
            embeddings = self.sentence_model.encode(
                combined_texts,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Assign embeddings to features
            for i, features in enumerate(features_list):
                features.text_embeddings = embeddings[i]
                
        except Exception as e:
            logger.error(f"Error generating text embeddings: {e}")
            # Fallback to zeros
            for features in features_list:
                features.text_embeddings = np.zeros(SENTENCE_EMBEDDING_DIM)

    def process_menu_and_tags_features(self, features_list: List[RestaurantFeatures]) -> None:
        """Process menu highlights and tags using TF-IDF for exact dish/tag matching"""
        
        logger.info("Processing menu highlights and tags with TF-IDF + embeddings")
        
        # Prepare menu highlights and tags data
        menu_texts = []
        tag_texts = []
        
        for features in features_list:
            # Process menu highlights - join into text
            menu_items = features.menu_highlights or []
            menu_text = " ".join([str(item).lower().strip('"') for item in menu_items if item])
            menu_texts.append(menu_text if menu_text else "food")
            
            # Process tags - join into text
            tag_items = features.tags or []
            tag_text = " ".join([str(tag).lower().strip('"') for tag in tag_items if tag])
            tag_texts.append(tag_text if tag_text else "restaurant")
        
        try:
            # Fit/transform TF-IDF for menu highlights
            if not self.menu_tfidf_fitted:
                menu_tfidf_matrix = self.menu_tfidf.fit_transform(menu_texts)
                self.menu_tfidf_fitted = True
            else:
                menu_tfidf_matrix = self.menu_tfidf.transform(menu_texts)
            
            # Fit/transform TF-IDF for tags
            if not self.tags_tfidf_fitted:
                tags_tfidf_matrix = self.tags_tfidf.fit_transform(tag_texts)
                self.tags_tfidf_fitted = True
            else:
                tags_tfidf_matrix = self.tags_tfidf.transform(tag_texts)
            
            # Also get semantic embeddings for broader similarity
            combined_menu_tags = [f"{menu} {tag}" for menu, tag in zip(menu_texts, tag_texts)]
            semantic_embeddings = self.sentence_model.encode(
                combined_menu_tags,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Assign combined features to each restaurant
            for i, features in enumerate(features_list):
                # Combine TF-IDF vectors with semantic embeddings
                menu_tfidf_vec = menu_tfidf_matrix[i].toarray().flatten()
                tags_tfidf_vec = tags_tfidf_matrix[i].toarray().flatten()
                semantic_vec = semantic_embeddings[i]
                
                # Concatenate all features (will scale them later)
                combined_features = np.concatenate([
                    menu_tfidf_vec,
                    tags_tfidf_vec, 
                    semantic_vec * SEMANTIC_EMBEDDING_WEIGHT  # Weight semantic features less than exact matches
                ])
                
                features.menu_tags_embeddings = combined_features
                
                logger.debug(f"{features.name}: menu_items={len(features.menu_highlights)}, tags={len(features.tags)}, feature_dim={len(combined_features)}")
                
        except Exception as e:
            logger.error(f"Error processing menu/tags: {e}")
            # Fallback to zero vectors
            fallback_dim = MENU_TFIDF_MAX_FEATURES + TAGS_TFIDF_MAX_FEATURES + SENTENCE_EMBEDDING_DIM
            for features in features_list:
                features.menu_tags_embeddings = np.zeros(fallback_dim)

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
                
                # 3. Text similarity (description + review)
                if (city_restaurant.text_embeddings is not None and 
                    user_restaurant.text_embeddings is not None):
                    text_sim = cosine_similarity(
                        [city_restaurant.text_embeddings], 
                        [user_restaurant.text_embeddings]
                    )[0][0]
                    text_sim = (text_sim + COSINE_SIM_NORMALIZATION_OFFSET) / 2
                else:
                    text_sim = NEUTRAL_SIMILARITY_SCORE
                scores['description'] = text_sim
                
                # 4. Menu/tags similarity (TF-IDF + semantic combination)
                if (city_restaurant.menu_tags_embeddings is not None and 
                    user_restaurant.menu_tags_embeddings is not None):
                    
                    # Ensure both vectors have same dimension
                    city_vec = city_restaurant.menu_tags_embeddings
                    user_vec = user_restaurant.menu_tags_embeddings
                    
                    if len(city_vec) == len(user_vec):
                        menu_sim = cosine_similarity([city_vec], [user_vec])[0][0]
                        menu_sim = max(0, (menu_sim + 1) / 2)  # Ensure positive
                    else:
                        logger.warning(f"Menu/tags vector dimension mismatch: {len(city_vec)} vs {len(user_vec)}")
                        menu_sim = 0.5
                else:
                    menu_sim = 0.5
                scores['menu_tags'] = menu_sim
                
                # Calculate weighted similarity
                weighted_sim = (
                    scores['cuisine'] * self.feature_weights['cuisine'] +
                    scores['price'] * self.feature_weights['price'] +
                    scores['description'] * self.feature_weights['description'] +
                    scores['menu_tags'] * self.feature_weights['menu_tags']
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
            
            # Identify matched features (above threshold)
            matched_features = []
            threshold = 0.5
            for feature, score in feature_scores.items():
                if score > threshold:
                    matched_features.append(f"{feature} ({score:.2f})")
            
            city_restaurant_scores.append({
                'restaurant': city_restaurant,
                'similarity': max_similarity,
                'feature_scores': feature_scores,
                'matched_features': matched_features,
                'best_user_match': user_restaurants[best_user_match].name
            })
        
        # Sort by similarity and take top k
        city_restaurant_scores.sort(key=lambda x: x['similarity'], reverse=True)
        top_recommendations = city_restaurant_scores[:top_k]
        
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
                feature_scores=rec['feature_scores'],
                matched_features=rec['matched_features']
            ))
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

# Global instance
recommendation_system = RestaurantRecommendationSystem()