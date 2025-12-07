"""Configuration management for the application"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings"""
    
    # Application
    app_name: str = "Model Deployment Tutorial"
    app_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "dev")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Model
    model_path: str = os.getenv("MODEL_PATH", "model.txt")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # AWS Configuration
    aws_region: str = os.getenv("AWS_REGION", "eu-central-1")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # S3 Configuration
    s3_bucket: Optional[str] = os.getenv("S3_BUCKET")
    s3_model_path: Optional[str] = os.getenv("S3_MODEL_PATH", "models/model.txt")
    
    # CloudWatch Configuration
    cloudwatch_log_group: str = os.getenv("CLOUDWATCH_LOG_GROUP", "model-deployment-tutorial")
    cloudwatch_log_stream: str = os.getenv("CLOUDWATCH_LOG_STREAM", "api")
    enable_cloudwatch: bool = os.getenv("ENABLE_CLOUDWATCH", "false").lower() == "true"
    
    # Athena Configuration
    athena_database: Optional[str] = os.getenv("ATHENA_DATABASE")
    athena_table: Optional[str] = os.getenv("ATHENA_TABLE", "model_predictions")
    athena_s3_output: Optional[str] = os.getenv("ATHENA_S3_OUTPUT")
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    enable_redis: bool = os.getenv("ENABLE_REDIS", "false").lower() == "true"
    
    # Monitoring
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "9090"))
    
    # Feature Store
    enable_feature_store: bool = os.getenv("ENABLE_FEATURE_STORE", "false").lower() == "true"


# Global settings instance
settings = Settings()

