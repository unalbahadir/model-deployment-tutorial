"""Model loading and inference utilities"""
import logging
import time
import os
from typing import List, Optional, Dict, Any
import numpy as np
import lightgbm as lgb
import boto3
from botocore.exceptions import ClientError

from src.config import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    """Handles model loading and inference"""
    
    def __init__(self):
        self.model: Optional[lgb.Booster] = None
        self.model_version: Optional[str] = None
        self.model_loaded: bool = False
        self._load_model()
    
    def _load_model_from_local(self, model_path: str) -> Optional[lgb.Booster]:
        """Load model from local file system"""
        try:
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None
            
            logger.info(f"Loading model from local path: {model_path}")
            model = lgb.Booster(model_file=model_path)
            self.model_version = f"local-{os.path.getmtime(model_path)}"
            logger.info(f"Model loaded successfully. Version: {self.model_version}")
            return model
        except Exception as e:
            logger.error(f"Error loading model from local path: {e}", exc_info=True)
            return None
    
    def _load_model_from_s3(self, bucket: str, key: str) -> Optional[lgb.Booster]:
        """Load model from S3"""
        try:
            logger.info(f"Loading model from S3: s3://{bucket}/{key}")
            s3_client = boto3.client(
                's3',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            
            # Download model to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                s3_client.download_fileobj(bucket, key, tmp_file)
                tmp_path = tmp_file.name
            
            # Load model from temporary file
            model = lgb.Booster(model_file=tmp_path)
            
            # Get model version from S3 object metadata
            try:
                response = s3_client.head_object(Bucket=bucket, Key=key)
                self.model_version = response.get('ETag', 'unknown')
            except:
                self.model_version = f"s3-{bucket}-{key}"
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            logger.info(f"Model loaded successfully from S3. Version: {self.model_version}")
            return model
        except ClientError as e:
            logger.error(f"AWS S3 error loading model: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error loading model from S3: {e}", exc_info=True)
            return None
    
    def _load_model(self):
        """Load model from configured source"""
        # Try S3 first if configured
        if settings.s3_bucket and settings.s3_model_path:
            self.model = self._load_model_from_s3(settings.s3_bucket, settings.s3_model_path)
            if self.model:
                self.model_loaded = True
                return
        
        # Fall back to local file
        model_path = settings.model_path
        self.model = self._load_model_from_local(model_path)
        if self.model:
            self.model_loaded = True
        else:
            logger.error("Failed to load model from both S3 and local path")
            self.model_loaded = False
    
    def reload_model(self):
        """Reload model (useful for model updates)"""
        logger.info("Reloading model...")
        self.model = None
        self.model_version = None
        self.model_loaded = False
        self._load_model()
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Make prediction with the model
        
        Args:
            features: Feature array of shape (n_samples, n_features)
            
        Returns:
            Prediction probabilities
        """
        if not self.model_loaded or self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            predictions = self.model.predict(features)
            return predictions
        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            raise
    
    def predict_batch(self, features_list: List[np.ndarray]) -> List[np.ndarray]:
        """
        Make batch predictions
        
        Args:
            features_list: List of feature arrays
            
        Returns:
            List of prediction arrays
        """
        if not self.model_loaded or self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Stack all features into single array
            features = np.vstack(features_list)
            predictions = self.predict(features)
            
            # Split predictions back into list
            results = []
            idx = 0
            for feat_array in features_list:
                n_samples = len(feat_array)
                results.append(predictions[idx:idx+n_samples])
                idx += n_samples
            
            return results
        except Exception as e:
            logger.error(f"Error during batch prediction: {e}", exc_info=True)
            raise


# Global model loader instance
model_loader = ModelLoader()

