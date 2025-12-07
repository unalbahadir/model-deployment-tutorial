# Quick Start Guide

Get up and running with the model deployment tutorial in 5 minutes!

## Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)
- AWS Account (optional, for cloud deployment)

## Step 1: Clone and Setup

```bash
cd model_deployment_monitoring_tutorial
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Verify Model File

Make sure `model.txt` exists in the project root:

```bash
ls -lh model.txt
```

## Step 3: Run the API

```bash
python -m uvicorn src.api:app --reload
```

The API will be available at: http://localhost:8000

## Step 4: Test the API

### Health Check

```bash
curl http://localhost:8000/health
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

### View API Documentation

Open in browser: http://localhost:8000/docs

## Step 5: Run with Docker (Optional)

```bash
# Build image
docker build -t model-deployment-tutorial .

# Run container
docker run -p 8000:8000 model-deployment-tutorial
```

## Step 6: View Metrics

```bash
curl http://localhost:8000/metrics
```

## Next Steps

1. **Read the full README**: See `README.md` for detailed documentation
2. **Follow the training**: Check `training/` directory for training materials
3. **Set up AWS**: See `training/AWS_SETUP_GUIDE.md` for AWS account setup
4. **Deploy to cloud**: Follow deployment guides in `README.md`

## Troubleshooting

### Model not loading?

- Check that `model.txt` exists
- Verify file permissions
- Check logs for error messages

### Port already in use?

```bash
# Use a different port
python -m uvicorn src.api:app --port 8001
```

### Import errors?

```bash
# Make sure you're in the project root
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Need Help?

- Check `README.md` for detailed documentation
- Review `training/` materials
- Check API docs at http://localhost:8000/docs

