"""Feature extraction utilities"""
import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

from src.schemas import PredictionRequest

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extracts features from request data for model inference"""
    
    # Feature order matching the model (from model.txt feature_names)
    FEATURE_ORDER = [
        'age', 'gender', 'Action', 'Adventure', 'Animation', "Children's", 'Comedy',
        'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror',
        'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western',
        'occupation_new', 'user_total_ratings', 'user_liked_ratings',
        'movie_total_ratings', 'movie_liked_ratings', 'occupation_movie_total',
        'occupation_movie_liked', 'user_genre_total', 'user_genre_liked',
        'user_like_rate', 'user_genre_like_rate', 'movie_like_rate',
        'occupation_like_rate', 'release_year'
    ]
    
    def __init__(self):
        # Gender encoding: M=1, F=0
        self.gender_map = {'M': 1, 'F': 0}
    
    def extract_features(self, request: PredictionRequest) -> np.ndarray:
        """
        Extract features from prediction request
        
        Args:
            request: PredictionRequest object
            
        Returns:
            Feature array of shape (1, n_features)
        """
        try:
            # Convert request to dict
            data = request.model_dump(by_alias=True)
            
            # Handle gender encoding
            gender_value = self.gender_map.get(data.get('gender', 'M'), 1)
            
            # Build feature array in correct order
            features = []
            for feature_name in self.FEATURE_ORDER:
                if feature_name == 'gender':
                    features.append(gender_value)
                elif feature_name == "Children's":
                    features.append(data.get('Childrens', 0))
                elif feature_name == 'Film-Noir':
                    features.append(data.get('FilmNoir', 0))
                elif feature_name == 'Sci-Fi':
                    features.append(data.get('SciFi', 0))
                else:
                    value = data.get(feature_name, 0)
                    # Handle None values
                    if value is None:
                        if feature_name in ['user_like_rate', 'user_genre_like_rate', 
                                          'movie_like_rate', 'occupation_like_rate']:
                            value = 0.0
                        elif feature_name == 'release_year':
                            value = 0.0
                        else:
                            value = 0
                    features.append(float(value))
            
            feature_array = np.array(features, dtype=np.float32).reshape(1, -1)
            
            return feature_array
        except Exception as e:
            logger.error(f"Error extracting features: {e}", exc_info=True)
            raise
    
    def extract_batch_features(self, requests: List[PredictionRequest]) -> np.ndarray:
        """
        Extract features from batch of requests
        
        Args:
            requests: List of PredictionRequest objects
            
        Returns:
            Feature array of shape (n_samples, n_features)
        """
        feature_arrays = []
        for request in requests:
            features = self.extract_features(request)
            feature_arrays.append(features)
        
        return np.vstack(feature_arrays)


# Global feature extractor instance
feature_extractor = FeatureExtractor()

