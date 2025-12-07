"""
Data pipeline components for storing predictions and metrics
Enhanced with S3 Parquet storage and Athena integration
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)

# S3 and Athena clients (lazy initialization)
_s3_client: Optional[boto3.client] = None
_athena_client: Optional[boto3.client] = None


def get_s3_client():
    """Get or create S3 client"""
    global _s3_client
    if _s3_client is None:
        try:
            _s3_client = boto3.client(
                's3',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        except Exception as e:
            logger.warning(f"Failed to create S3 client: {e}")
            _s3_client = None
    return _s3_client


def get_athena_client():
    """Get or create Athena client"""
    global _athena_client
    if _athena_client is None:
        try:
            _athena_client = boto3.client(
                'athena',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        except Exception as e:
            logger.warning(f"Failed to create Athena client: {e}")
            _athena_client = None
    return _athena_client


def save_prediction_to_s3(
    prediction_data: Dict[str, Any],
    s3_bucket: Optional[str] = None,
    s3_prefix: str = "predictions"
) -> bool:
    """
    Save prediction data to S3 in Parquet format with partitioning
    
    Args:
        prediction_data: Dictionary containing prediction data
        s3_bucket: S3 bucket name (uses config if not provided)
        s3_prefix: S3 prefix (folder path)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        bucket = s3_bucket or settings.s3_bucket
        if not bucket:
            logger.warning("S3 bucket not configured, skipping save")
            return False
        
        s3 = get_s3_client()
        if s3 is None:
            logger.warning("S3 client not available, skipping save")
            return False
        
        # Create DataFrame from prediction data
        df = pd.DataFrame([prediction_data])
        
        # Generate S3 key with timestamp for partitioning
        timestamp = datetime.utcnow()
        date_partition = timestamp.strftime("%Y/%m/%d")
        hour_partition = timestamp.strftime("%H")
        s3_key = f"{s3_prefix}/{date_partition}/{hour_partition}/prediction_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.parquet"
        
        # Convert DataFrame to Parquet bytes
        parquet_buffer = df.to_parquet(index=False, engine='pyarrow')
        
        # Upload to S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=parquet_buffer,
            ContentType='application/octet-stream'
        )
        
        logger.info(f"Saved prediction to s3://{bucket}/{s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save prediction to S3: {e}", exc_info=True)
        return False


def save_batch_predictions_to_s3(
    predictions: List[Dict[str, Any]],
    s3_bucket: Optional[str] = None,
    s3_prefix: str = "predictions"
) -> bool:
    """
    Save batch predictions to S3 in Parquet format
    
    Args:
        predictions: List of prediction dictionaries
        s3_bucket: S3 bucket name (uses config if not provided)
        s3_prefix: S3 prefix (folder path)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        bucket = s3_bucket or settings.s3_bucket
        if not bucket:
            logger.warning("S3 bucket not configured, skipping save")
            return False
        
        s3 = get_s3_client()
        if s3 is None:
            logger.warning("S3 client not available, skipping save")
            return False
        
        if not predictions:
            logger.warning("Empty predictions list, skipping save")
            return False
        
        # Create DataFrame from predictions
        df = pd.DataFrame(predictions)
        
        # Generate S3 key with timestamp for partitioning
        timestamp = datetime.utcnow()
        date_partition = timestamp.strftime("%Y/%m/%d")
        hour_partition = timestamp.strftime("%H")
        s3_key = f"{s3_prefix}/{date_partition}/{hour_partition}/batch_predictions_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.parquet"
        
        # Convert DataFrame to Parquet bytes
        parquet_buffer = df.to_parquet(index=False, engine='pyarrow')
        
        # Upload to S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=parquet_buffer,
            ContentType='application/octet-stream'
        )
        
        logger.info(f"Saved {len(predictions)} predictions to s3://{bucket}/{s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save batch predictions to S3: {e}", exc_info=True)
        return False


def query_predictions_from_athena(
    database: Optional[str] = None,
    table: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query predictions from Athena
    
    Args:
        database: Athena database name (uses config if not provided)
        table: Athena table name (uses config if not provided)
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        user_id: Optional user ID filter
        limit: Maximum number of results
    
    Returns:
        List of prediction records or query execution info
    """
    try:
        db = database or settings.athena_database
        tbl = table or settings.athena_table
        
        if not db or not tbl:
            logger.warning("Athena database or table not configured")
            return []
        
        athena = get_athena_client()
        if athena is None:
            logger.warning("Athena client not available")
            return []
        
        # Build query
        query = f"SELECT * FROM {db}.{tbl} WHERE 1=1"
        
        if start_date:
            query += f" AND date >= '{start_date}'"
        if end_date:
            query += f" AND date <= '{end_date}'"
        if user_id:
            query += f" AND user_id = {user_id}"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        # Execute query
        output_location = settings.athena_s3_output or f"s3://{settings.s3_bucket}/athena-results/"
        
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': db},
            ResultConfiguration={'OutputLocation': output_location}
        )
        
        query_execution_id = response['QueryExecutionId']
        logger.info(f"Started Athena query: {query_execution_id}")
        
        # Note: In production, you would poll for query completion
        # For demo purposes, we'll just return the query ID
        return [{'query_execution_id': query_execution_id, 'status': 'RUNNING', 'query': query}]
        
    except Exception as e:
        logger.error(f"Failed to query Athena: {e}", exc_info=True)
        return []

