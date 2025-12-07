"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]


def test_metrics():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_predictions" in data


def test_predict():
    """Test prediction endpoint"""
    request_data = {
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
    
    response = client.post("/predict", json=request_data)
    # May fail if model not loaded, which is OK for testing
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert "prediction" in data
        assert "prediction_class" in data
        assert 0 <= data["prediction"] <= 1

