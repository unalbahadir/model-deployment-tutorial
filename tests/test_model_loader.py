"""Unit tests for model loader"""
import pytest
import os
from src.model_loader import model_loader


def test_model_loaded():
    """Test that model loads successfully"""
    assert model_loader.model_loaded is True, "Model should be loaded"
    assert model_loader.model is not None, "Model object should exist"


def test_model_version():
    """Test model version retrieval"""
    version = model_loader.model_version
    assert version is not None, "Model version should be set"
    assert isinstance(version, str), "Model version should be a string"
    assert len(version) > 0, "Model version should not be empty"


def test_model_predict():
    """Test model prediction functionality"""
    import numpy as np
    
    # Create sample features matching the model's expected input
    # The model expects 34 features (from feature_names in model.txt)
    sample_features = np.array([[
        21.0,  # age
        1.0,   # gender (M=1, F=0)
        0.0,   # Action
        1.0,   # Adventure
        0.0,   # Animation
        0.0,   # Children's
        0.0,   # Comedy
        0.0,   # Crime
        0.0,   # Documentary
        0.0,   # Drama
        0.0,   # Fantasy
        0.0,   # Film-Noir
        0.0,   # Horror
        0.0,   # Musical
        0.0,   # Mystery
        0.0,   # Romance
        0.0,   # Sci-Fi
        0.0,   # Thriller
        1.0,   # War
        0.0,   # Western
        0.0,   # occupation_new (encoded)
        2.0,   # user_total_ratings
        2.0,   # user_liked_ratings
        0.0,   # movie_total_ratings
        0.0,   # movie_liked_ratings
        2.0,   # occupation_movie_total
        2.0,   # occupation_movie_liked
        5.0,   # user_genre_total
        5.0,   # user_genre_liked
        1.0,   # user_like_rate
        1.0,   # user_genre_like_rate
        0.0,   # movie_like_rate
        1.0,   # occupation_like_rate
        1997.0 # release_year
    ]], dtype=np.float32)
    
    if model_loader.model_loaded:
        predictions = model_loader.predict(sample_features)
        assert len(predictions) == 1, "Should return one prediction"
        assert 0.0 <= predictions[0] <= 1.0, "Prediction should be between 0 and 1"
    else:
        pytest.skip("Model not loaded, skipping prediction test")


def test_model_reload():
    """Test model reload functionality"""
    if model_loader.model_loaded:
        original_version = model_loader.model_version
        model_loader.reload_model()
        # After reload, model should still be loaded
        assert model_loader.model_loaded is True, "Model should still be loaded after reload"
        # Version might change if model file was updated
        assert model_loader.model_version is not None, "Model version should be set"
    else:
        pytest.skip("Model not loaded, skipping reload test")


def test_model_file_exists():
    """Test that model file exists"""
    model_path = "model.txt"
    assert os.path.exists(model_path), f"Model file should exist at {model_path}"

