"""Pydantic schemas for request/response validation"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import numpy as np


class PredictionRequest(BaseModel):
    """Request schema for model predictions"""
    user_id: int = Field(..., description="User ID")
    movie_id: int = Field(..., description="Movie ID")
    age: int = Field(..., ge=1, le=100, description="User age")
    gender: str = Field(..., pattern="^[MF]$", description="User gender (M or F)")
    occupation_new: str = Field(..., description="User occupation")
    release_year: Optional[float] = Field(None, description="Movie release year")
    
    # Genre features (binary)
    Action: int = Field(0, ge=0, le=1)
    Adventure: int = Field(0, ge=0, le=1)
    Animation: int = Field(0, ge=0, le=1)
    Childrens: int = Field(0, ge=0, le=1, alias="Children's")
    Comedy: int = Field(0, ge=0, le=1)
    Crime: int = Field(0, ge=0, le=1)
    Documentary: int = Field(0, ge=0, le=1)
    Drama: int = Field(0, ge=0, le=1)
    Fantasy: int = Field(0, ge=0, le=1)
    FilmNoir: int = Field(0, ge=0, le=1, alias="Film-Noir")
    Horror: int = Field(0, ge=0, le=1)
    Musical: int = Field(0, ge=0, le=1)
    Mystery: int = Field(0, ge=0, le=1)
    Romance: int = Field(0, ge=0, le=1)
    SciFi: int = Field(0, ge=0, le=1, alias="Sci-Fi")
    Thriller: int = Field(0, ge=0, le=1)
    War: int = Field(0, ge=0, le=1)
    Western: int = Field(0, ge=0, le=1)
    
    # Aggregated features
    user_total_ratings: int = Field(0, ge=0)
    user_liked_ratings: int = Field(0, ge=0)
    movie_total_ratings: int = Field(0, ge=0)
    movie_liked_ratings: int = Field(0, ge=0)
    occupation_movie_total: int = Field(0, ge=0)
    occupation_movie_liked: int = Field(0, ge=0)
    user_genre_total: int = Field(0, ge=0)
    user_genre_liked: int = Field(0, ge=0)
    user_like_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    user_genre_like_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    movie_like_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    occupation_like_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": 259,
                "movie_id": 298,
                "age": 21,
                "gender": "M",
                "occupation_new": "student",
                "release_year": 1997.0,
                "Action": 0,
                "Adventure": 1,
                "Animation": 0,
                "Children's": 0,
                "Comedy": 0,
                "Crime": 0,
                "Documentary": 0,
                "Drama": 0,
                "Fantasy": 0,
                "Film-Noir": 0,
                "Horror": 0,
                "Musical": 0,
                "Mystery": 0,
                "Romance": 0,
                "Sci-Fi": 0,
                "Thriller": 0,
                "War": 1,
                "Western": 0,
                "user_total_ratings": 2,
                "user_liked_ratings": 2,
                "movie_total_ratings": 0,
                "movie_liked_ratings": 0,
                "occupation_movie_total": 2,
                "occupation_movie_liked": 2,
                "user_genre_total": 5,
                "user_genre_liked": 5,
                "user_like_rate": 1.0,
                "user_genre_like_rate": 1.0,
                "movie_like_rate": None,
                "occupation_like_rate": 1.0
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions"""
    predictions: List[PredictionRequest] = Field(..., min_items=1, max_items=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "predictions": [
                    {
                        "user_id": 259,
                        "movie_id": 298,
                        "age": 21,
                        "gender": "M",
                        "occupation_new": "student",
                        "release_year": 1997.0
                    }
                ]
            }
        }


class PredictionResponse(BaseModel):
    """Response schema for model predictions"""
    user_id: int
    movie_id: int
    prediction: float = Field(..., ge=0.0, le=1.0, description="Predicted probability")
    prediction_class: int = Field(..., ge=0, le=1, description="Predicted class (0 or 1)")
    model_version: str
    inference_time_ms: float


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""
    predictions: List[PredictionResponse]
    total_time_ms: float
    avg_time_per_prediction_ms: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    model_version: Optional[str] = None
    environment: str


class MetricsResponse(BaseModel):
    """Metrics response"""
    total_requests: int
    total_predictions: int
    avg_inference_time_ms: float
    p95_inference_time_ms: float
    p99_inference_time_ms: float
    error_rate: float
    requests_per_second: float

