"""FastAPI application for model serving"""
import logging
import time
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.schemas import (
    PredictionRequest, BatchPredictionRequest,
    PredictionResponse, BatchPredictionResponse,
    HealthResponse, MetricsResponse
)
from src.model_loader import model_loader
from src.feature_extractor import feature_extractor
from src.monitoring import metrics_collector, cloudwatch_logger
from src.data_pipeline import save_prediction_to_s3, save_batch_predictions_to_s3

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Model loaded: {model_loader.model_loaded}")
    
    if not model_loader.model_loaded:
        logger.error("Model failed to load! Service may not work correctly.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Model Deployment and Monitoring Tutorial - Movie Recommendation Model",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return HealthResponse(
        status="ok",
        model_loaded=model_loader.model_loaded,
        model_version=model_loader.model_version,
        environment=settings.environment
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok" if model_loader.model_loaded else "degraded",
        model_loaded=model_loader.model_loaded,
        model_version=model_loader.model_version,
        environment=settings.environment
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a single prediction
    
    Returns:
        PredictionResponse with prediction probability and class
    """
    if not model_loader.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    metrics_collector.record_request()
    start_time = time.time()
    
    try:
        # Extract features
        features = feature_extractor.extract_features(request)
        
        # Make prediction
        predictions = model_loader.predict(features)
        prediction_prob = float(predictions[0])
        prediction_class = 1 if prediction_prob >= 0.5 else 0
        
        inference_time_ms = (time.time() - start_time) * 1000
        request_time_ms = inference_time_ms  # For single prediction, they're the same
        
        # Record metrics
        metrics_collector.record_prediction(inference_time_ms, success=True, request_time_ms=request_time_ms)
        
        # Log to monitoring systems
        cloudwatch_logger.log_prediction(
            request.user_id, request.movie_id, prediction_prob,
            inference_time_ms, model_loader.model_version or "unknown"
        )
        
        # Save to S3 for analytics (async, non-blocking)
        # This data can be queried via Athena
        if settings.s3_bucket:
            prediction_data = {
                "user_id": request.user_id,
                "movie_id": request.movie_id,
                "age": request.age,
                "gender": request.gender,
                "prediction": prediction_prob,
                "prediction_class": prediction_class,
                "model_version": model_loader.model_version or "unknown",
                "inference_time_ms": inference_time_ms,
                "timestamp": time.time()
            }
            save_prediction_to_s3(prediction_data)
        
        return PredictionResponse(
            user_id=request.user_id,
            movie_id=request.movie_id,
            prediction=prediction_prob,
            prediction_class=prediction_class,
            model_version=model_loader.model_version or "unknown",
            inference_time_ms=round(inference_time_ms, 3)
        )
    
    except Exception as e:
        inference_time_ms = (time.time() - start_time) * 1000
        request_time_ms = inference_time_ms
        metrics_collector.record_prediction(inference_time_ms, success=False, request_time_ms=request_time_ms)
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Make batch predictions
    
    Returns:
        BatchPredictionResponse with list of predictions
    """
    if not model_loader.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    metrics_collector.record_request()
    start_time = time.time()
    
    try:
        # Extract features for all requests
        features = feature_extractor.extract_batch_features(request.predictions)
        
        # Make batch predictions
        predictions = model_loader.predict(features)
        
        # Build response
        response_predictions = []
        for i, pred_request in enumerate(request.predictions):
            prediction_prob = float(predictions[i])
            prediction_class = 1 if prediction_prob >= 0.5 else 0
            
            response_predictions.append(PredictionResponse(
                user_id=pred_request.user_id,
                movie_id=pred_request.movie_id,
                prediction=prediction_prob,
                prediction_class=prediction_class,
                model_version=model_loader.model_version or "unknown",
                inference_time_ms=0.0  # Batch inference time is in total_time_ms
            ))
        
        total_time_ms = (time.time() - start_time) * 1000
        avg_time_per_prediction_ms = total_time_ms / len(request.predictions)
        
        # Record metrics for each prediction
        for _ in request.predictions:
            metrics_collector.record_prediction(avg_time_per_prediction_ms, success=True, request_time_ms=avg_time_per_prediction_ms)
        
        # Save batch predictions to S3 for analytics (async, non-blocking)
        if settings.s3_bucket:
            batch_data = []
            for i, pred_request in enumerate(request.predictions):
                prediction_prob = float(predictions[i])
                prediction_class = 1 if prediction_prob >= 0.5 else 0
                batch_data.append({
                    "user_id": pred_request.user_id,
                    "movie_id": pred_request.movie_id,
                    "age": pred_request.age,
                    "gender": pred_request.gender,
                    "prediction": prediction_prob,
                    "prediction_class": prediction_class,
                    "model_version": model_loader.model_version or "unknown",
                    "inference_time_ms": avg_time_per_prediction_ms,
                    "timestamp": time.time()
                })
            save_batch_predictions_to_s3(batch_data)
        
        return BatchPredictionResponse(
            predictions=response_predictions,
            total_time_ms=round(total_time_ms, 3),
            avg_time_per_prediction_ms=round(avg_time_per_prediction_ms, 3)
        )
    
    except Exception as e:
        total_time_ms = (time.time() - start_time) * 1000
        avg_time_per_prediction_ms = total_time_ms / len(request.predictions) if request.predictions else 0
        metrics_collector.record_prediction(avg_time_per_prediction_ms, success=False, request_time_ms=avg_time_per_prediction_ms)
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get application metrics"""
    metrics = metrics_collector.get_metrics()
    return MetricsResponse(**metrics)


@app.post("/model/reload")
async def reload_model():
    """Reload model (useful for model updates)"""
    try:
        model_loader.reload_model()
        if model_loader.model_loaded:
            return {"status": "success", "message": "Model reloaded successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload model"
            )
    except Exception as e:
        logger.error(f"Model reload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model reload failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )

