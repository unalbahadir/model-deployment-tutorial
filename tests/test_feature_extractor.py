"""Unit tests for feature extractor"""
import pytest
import numpy as np
from src.feature_extractor import feature_extractor
from src.schemas import PredictionRequest


def test_extract_features():
    """Test feature extraction from request"""
    request = PredictionRequest(
        user_id=259,
        movie_id=298,
        age=21,
        gender="M",
        occupation_new="student",
        release_year=1997.0,
        Action=0,
        Adventure=1,
        War=1,
        user_total_ratings=2,
        user_liked_ratings=2,
        user_like_rate=1.0,
        user_genre_like_rate=1.0,
        occupation_like_rate=1.0
    )
    
    features = feature_extractor.extract_features(request)
    
    assert features is not None, "Features should be extracted"
    assert isinstance(features, np.ndarray), "Features should be numpy array"
    assert features.shape == (1, 34), f"Features should have shape (1, 34), got {features.shape}"
    assert features.dtype == np.float32, "Features should be float32"


def test_extract_batch_features():
    """Test batch feature extraction"""
    requests = [
        PredictionRequest(
            user_id=259,
            movie_id=298,
            age=21,
            gender="M",
            occupation_new="student",
            release_year=1997.0,
            Action=0,
            Adventure=1
        ),
        PredictionRequest(
            user_id=260,
            movie_id=299,
            age=25,
            gender="F",
            occupation_new="engineer",
            release_year=1995.0,
            Action=1,
            Adventure=0
        )
    ]
    
    features = feature_extractor.extract_batch_features(requests)
    
    assert features is not None, "Features should be extracted"
    assert isinstance(features, np.ndarray), "Features should be numpy array"
    assert features.shape == (2, 34), f"Features should have shape (2, 34), got {features.shape}"


def test_gender_encoding():
    """Test gender encoding (M=1, F=0)"""
    request_m = PredictionRequest(
        user_id=1,
        movie_id=1,
        age=25,
        gender="M",
        occupation_new="student"
    )
    
    request_f = PredictionRequest(
        user_id=2,
        movie_id=2,
        age=25,
        gender="F",
        occupation_new="student"
    )
    
    features_m = feature_extractor.extract_features(request_m)
    features_f = feature_extractor.extract_features(request_f)
    
    # Gender is the second feature (index 1)
    assert features_m[0, 1] == 1.0, "Male should be encoded as 1"
    assert features_f[0, 1] == 0.0, "Female should be encoded as 0"


def test_none_values_handling():
    """Test that None values are handled correctly"""
    request = PredictionRequest(
        user_id=1,
        movie_id=1,
        age=25,
        gender="M",
        occupation_new="student",
        release_year=None,  # None value
        user_like_rate=None,
        movie_like_rate=None
    )
    
    features = feature_extractor.extract_features(request)
    
    # Should not raise an error and should handle None values
    assert features is not None, "Features should be extracted even with None values"
    assert not np.isnan(features).any(), "Features should not contain NaN values"

