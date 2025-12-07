"""Monitoring and metrics collection"""
import logging
import time
from typing import Dict, Any, Optional
from collections import deque
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from src.config import settings

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_predictions = 0
        self.total_errors = 0
        self.inference_times = deque(maxlen=10000)  # Keep last 10k inference times
        self.start_time = time.time()
    
    def record_prediction(self, inference_time_ms: float, success: bool = True, request_time_ms: Optional[float] = None):
        """Record a prediction metric"""
        self.total_predictions += 1
        if success:
            self.inference_times.append(inference_time_ms)
        else:
            self.total_errors += 1
        
        # Send metrics to CloudWatch if enabled
        if cloudwatch_metrics.enabled:
            cloudwatch_metrics.put_metric('InferenceTime', inference_time_ms, 'Milliseconds')
            if request_time_ms:
                cloudwatch_metrics.put_metric('RequestTime', request_time_ms, 'Milliseconds')
            cloudwatch_metrics.put_metric('RequestCount', 1, 'Count')
            if not success:
                cloudwatch_metrics.put_metric('ErrorCount', 1, 'Count')
    
    def record_request(self):
        """Record a request"""
        self.total_requests += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        if not self.inference_times:
            return {
                "total_requests": self.total_requests,
                "total_predictions": self.total_predictions,
                "total_errors": self.total_errors,
                "avg_inference_time_ms": 0.0,
                "p95_inference_time_ms": 0.0,
                "p99_inference_time_ms": 0.0,
                "error_rate": 0.0,
                "requests_per_second": 0.0
            }
        
        sorted_times = sorted(self.inference_times)
        n = len(sorted_times)
        
        avg_time = sum(sorted_times) / n
        p95_time = sorted_times[int(n * 0.95)]
        p99_time = sorted_times[int(n * 0.99)]
        
        elapsed_time = time.time() - self.start_time
        rps = self.total_requests / elapsed_time if elapsed_time > 0 else 0.0
        error_rate = self.total_errors / self.total_predictions if self.total_predictions > 0 else 0.0
        
        return {
            "total_requests": self.total_requests,
            "total_predictions": self.total_predictions,
            "total_errors": self.total_errors,
            "avg_inference_time_ms": round(avg_time, 3),
            "p95_inference_time_ms": round(p95_time, 3),
            "p99_inference_time_ms": round(p99_time, 3),
            "error_rate": round(error_rate, 4),
            "requests_per_second": round(rps, 2)
        }
    
    def reset(self):
        """Reset metrics"""
        self.total_requests = 0
        self.total_predictions = 0
        self.total_errors = 0
        self.inference_times.clear()
        self.start_time = time.time()


class CloudWatchMetrics:
    """CloudWatch metrics publisher"""
    
    def __init__(self):
        self.enabled = settings.enable_cloudwatch
        self.namespace = "ModelDeployment"
        self.client = None
        
        if self.enabled:
            try:
                self.client = boto3.client(
                    'cloudwatch',
                    region_name=settings.aws_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key
                )
                logger.info(f"CloudWatch metrics enabled: {self.namespace}")
            except Exception as e:
                logger.warning(f"Failed to initialize CloudWatch metrics: {e}")
                self.enabled = False
    
    def put_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        """
        Put a custom metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Count, Seconds, Milliseconds, Percent, etc.)
        """
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            logger.debug(f"Failed to put metric to CloudWatch: {e}")


class CloudWatchLogger:
    """CloudWatch logging handler"""
    
    def __init__(self):
        self.enabled = settings.enable_cloudwatch
        self.log_group = settings.cloudwatch_log_group
        self.log_stream = settings.cloudwatch_log_stream
        self.client = None
        
        if self.enabled:
            try:
                self.client = boto3.client(
                    'logs',
                    region_name=settings.aws_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key
                )
                self._ensure_log_group_exists()
                logger.info(f"CloudWatch logging enabled: {self.log_group}/{self.log_stream}")
            except Exception as e:
                logger.warning(f"Failed to initialize CloudWatch: {e}")
                self.enabled = False
    
    def _ensure_log_group_exists(self):
        """Ensure CloudWatch log group exists"""
        try:
            self.client.create_log_group(logGroupName=self.log_group)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise
    
    def log_prediction(self, user_id: int, movie_id: int, prediction: float, 
                      inference_time_ms: float, model_version: str):
        """Log prediction to CloudWatch"""
        if not self.enabled or not self.client:
            return
        
        try:
            log_message = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "prediction",
                "user_id": user_id,
                "movie_id": movie_id,
                "prediction": prediction,
                "inference_time_ms": inference_time_ms,
                "model_version": model_version
            }
            
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': str(log_message)
                }]
            )
        except Exception as e:
            logger.debug(f"Failed to log to CloudWatch: {e}")


# Note: Athena integration is handled via S3 storage in data_pipeline.py
# Predictions are saved to S3 using save_prediction_to_s3(), which can then be
# queried via Athena using the table created with scripts/create_athena_table.sql


# Global instances
metrics_collector = MetricsCollector()
cloudwatch_metrics = CloudWatchMetrics()
cloudwatch_logger = CloudWatchLogger()

