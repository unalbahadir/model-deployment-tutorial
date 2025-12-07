# Model Deployment and Monitoring Tutorial

A comprehensive tutorial project demonstrating production-ready model deployment and monitoring practices using LightGBM, FastAPI, Docker, Kubernetes, and AWS services.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Training Materials](#training-materials)
- [AWS Setup](#aws-setup)

## 🎯 Overview

This project demonstrates best practices for deploying and monitoring machine learning models in production. It includes:

- **Model Serving**: FastAPI-based REST API for real-time predictions
- **Containerization**: Docker and Kubernetes deployment configurations
- **CI/CD**: GitHub Actions and AWS CodeBuild/CodePipeline integration
- **Monitoring**: CloudWatch, Athena, and custom metrics
- **Scalability**: Horizontal scaling with Kubernetes

## ✨ Features

- ✅ **FastAPI REST API** for model inference
- ✅ **LightGBM Model** serving with batch prediction support
- ✅ **Docker** containerization
- ✅ **Kubernetes** deployment manifests with **HPA** (auto-scaling)
- ✅ **CI/CD** with GitHub Actions and AWS CodeBuild
- ✅ **CloudWatch** logging and monitoring
- ✅ **Athena** for querying prediction logs (with partitioned tables)
- ✅ **S3** model storage and prediction logging (Parquet format)
- ✅ **AWS ALB Ingress** for production routing
- ✅ **Health checks** and metrics endpoints
- ✅ **Feature extraction** and validation
- ✅ **Error handling** and logging
- ✅ **Load testing** script
- ✅ **Makefile** for convenient operations

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   FastAPI API   │
│   (Port 8000)    │
└──────┬──────────┘
       │
       ├──► Model Loader ──► LightGBM Model
       │
       ├──► Feature Extractor
       │
       ├──► Metrics Collector
       │
       ├──► CloudWatch Logger
       │
       └──► Data Pipeline ──► S3 ──► Athena
```

## 🚀 Quick Start

### Local Development

1. **Clone and setup**:
```bash
cd model_deployment_monitoring_tutorial
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run the API**:
```bash
python -m uvicorn src.api:app --reload
```

3. **Test the API**:
```bash
curl http://localhost:8000/health
```

### Docker

```bash
# Build image
docker build -t model-deployment-tutorial .

# Run container
docker run -p 8000:8000 model-deployment-tutorial

# Or use docker-compose
docker-compose up
```

### Make a Prediction

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 259,
    "movie_id": 298,
    "age": 21,
    "gender": "M",
    "occupation_new": "student",
    "release_year": 1997.0,
    "Action": 0,
    "Adventure": 1,
    "War": 1,
    "user_total_ratings": 2,
    "user_liked_ratings": 2,
    "user_like_rate": 1.0
  }'
```

## 📦 Deployment

### Docker

```bash
docker build -t model-deployment-tutorial .
docker run -p 8000:8000 \
  -e AWS_REGION=eu-central-1 \
  -e S3_BUCKET=your-bucket \
  model-deployment-tutorial
```

### Kubernetes

1. **Update image in deployment.yaml**:
```yaml
image: <YOUR_ECR_REGISTRY>/model-deployment-tutorial:latest
```

2. **Update secrets** (if using secrets.yaml):
```bash
# Edit k8s/secrets.yaml with your actual values
# Or use k8s/secrets.yaml.example as a template
```

3. **Apply manifests**:
```bash
# Deploy ConfigMap and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Deploy HPA for auto-scaling (optional)
kubectl apply -f k8s/hpa.yaml

# Deploy Ingress for external access (optional)
kubectl apply -f k8s/ingress.yaml
```

3. **Check status**:
```bash
kubectl get pods
kubectl get services
kubectl get hpa          # Check auto-scaling
kubectl get ingress      # Check ingress (if deployed)
```

**Or use Makefile:**
```bash
make k8s-deploy          # Deploy application
make k8s-apply-hpa       # Apply HPA
make k8s-apply-ingress   # Apply Ingress
```

### AWS ECS/Fargate

1. **Push to ECR**:
```bash
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com
docker tag model-deployment-tutorial:latest <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/model-deployment-tutorial:latest
docker push <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/model-deployment-tutorial:latest
```

2. **Create ECS service** using the ECR image

### CI/CD

#### GitHub Actions

Automatically builds and deploys on push to `main` branch. Configure secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### AWS CodeBuild/CodePipeline

1. **Create CodeBuild project** using `buildspec.yaml`
   - For testing: Use `buildspec.test.yaml` for test pipeline
   - For deployment: Use `buildspec.yaml` for build and deploy

2. **Create CodePipeline** with stages:
   - Source: GitHub repository
   - Build: CodeBuild (test) using `buildspec.test.yaml`
   - Build: CodeBuild (deploy) using `buildspec.yaml`
   - Deploy: Automatic (via buildspec) or manual approval

3. **Environment Variables** (set in CodeBuild):
   - `ECR_REPO_REGISTRY`: Your ECR registry URL
   - `APP_NAME`: model-deployment-tutorial
   - `AWS_DEFAULT_REGION`: eu-central-1
   - `EKS_CLUSTER_NAME`: Your EKS cluster name
   - `DEPLOY_TO_K8S`: true (to enable auto-deployment)

## 📊 Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

Returns:
- Total requests and predictions
- Average, P95, P99 inference times
- Error rate
- Requests per second

### CloudWatch

Enable CloudWatch logging and metrics:
```bash
export ENABLE_CLOUDWATCH=true
export AWS_REGION=eu-central-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

**Setup CloudWatch Dashboard:**
```bash
aws cloudwatch put-dashboard \
  --dashboard-name ModelDeployment \
  --dashboard-body file://scripts/setup_cloudwatch_dashboard.json
```

The application automatically sends metrics to CloudWatch:
- `RequestCount`: Total number of requests
- `ErrorCount`: Number of errors
- `InferenceTime`: Model inference time (ms)
- `RequestTime`: Total request time (ms)

### Athena

**Setup Athena table:**
```bash
# Update scripts/create_athena_table.sql with your bucket name
aws athena start-query-execution \
  --query-string "$(cat scripts/create_athena_table.sql)" \
  --result-configuration OutputLocation=s3://your-bucket/athena-results/
```

**Query prediction logs:**
```sql
-- Get recent predictions
SELECT * FROM model_predictions 
WHERE year = 2024 AND month = 12 
ORDER BY timestamp DESC 
LIMIT 100;

-- Get average prediction by user
SELECT user_id, AVG(prediction) as avg_prediction, COUNT(*) as prediction_count 
FROM model_predictions 
WHERE year = 2024 AND month = 12 
GROUP BY user_id 
ORDER BY prediction_count DESC 
LIMIT 10;
```

**Note:** Predictions are automatically saved to S3 in Parquet format with date/hour partitioning for efficient querying.

## 📚 Training Materials

See `training/` directory for:
- **Slides**: Presentation slides (PDF/PPTX)
- **Outline**: Training session outline
- **Exercises**: Hands-on exercises
- **AWS Setup Guide**: Step-by-step AWS account setup

## 🔧 Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (dev/prod) | `dev` |
| `DEBUG` | Debug mode | `false` |
| `MODEL_PATH` | Path to model file | `model.txt` |
| `AWS_REGION` | AWS region | `eu-central-1` |
| `S3_BUCKET` | S3 bucket for model | - |
| `ENABLE_CLOUDWATCH` | Enable CloudWatch logging | `false` |
| `ENABLE_REDIS` | Enable Redis caching | `false` |
| `ATHENA_DATABASE` | Athena database name | - |
| `ATHENA_TABLE` | Athena table name | `model_predictions` |

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_api.py -v
pytest tests/test_model_loader.py -v
pytest tests/test_feature_extractor.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Prediction (using test request file)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### Load Testing

```bash
# Using the load test script
./scripts/load_test.sh http://localhost:8000/predict 10 100

# Or use Makefile
make load-test
```

## 📖 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security

- Use IAM roles instead of access keys when possible
- Store secrets in AWS Secrets Manager or Kubernetes secrets
- Enable HTTPS in production
- Implement authentication/authorization
- Validate all inputs

## 📝 License

This project is for educational/tutorial purposes.

## 🤝 Contributing

This is a tutorial project. Feel free to use it as a reference for your own projects.

## 📞 Support

For questions or issues, refer to the training materials in the `training/` directory.

