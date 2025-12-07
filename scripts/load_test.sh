#!/bin/bash
# Load testing script using curl
# Usage: ./load_test.sh <endpoint> <concurrent_users> <requests_per_user>

ENDPOINT=${1:-"http://localhost:8000/predict"}
CONCURRENT_USERS=${2:-10}
REQUESTS_PER_USER=${3:-100}

echo "Starting load test..."
echo "Endpoint: $ENDPOINT"
echo "Concurrent users: $CONCURRENT_USERS"
echo "Requests per user: $REQUESTS_PER_USER"

# Sample prediction request JSON
PREDICTION_JSON='{
  "user_id": 259,
  "movie_id": 298,
  "age": 21,
  "gender": "M",
  "occupation_new": "student",
  "release_year": 1997.0,
  "Action": 0,
  "Adventure": 1,
  "Animation": 0,
  "Children'\''s": 0,
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
  "movie_like_rate": null,
  "occupation_like_rate": 1.0
}'

# Run load test using Apache Bench (ab) if available, otherwise use curl
if command -v ab &> /dev/null; then
    echo "Using Apache Bench for load testing..."
    echo "$PREDICTION_JSON" > /tmp/prediction.json
    ab -n $((CONCURRENT_USERS * REQUESTS_PER_USER)) -c $CONCURRENT_USERS -p /tmp/prediction.json -T application/json $ENDPOINT
    rm /tmp/prediction.json
else
    echo "Apache Bench not found. Using curl for basic testing..."
    echo "Note: For proper load testing, install Apache Bench:"
    echo "  macOS: brew install httpd"
    echo "  Ubuntu/Debian: apt-get install apache2-utils"
    echo "  CentOS/RHEL: yum install httpd-tools"
    
    START_TIME=$(date +%s)
    
    for i in $(seq 1 $CONCURRENT_USERS); do
        (
            for j in $(seq 1 $REQUESTS_PER_USER); do
                curl -s -X POST "$ENDPOINT" \
                    -H "Content-Type: application/json" \
                    -d "$PREDICTION_JSON" \
                    -w "\nTime: %{time_total}s\n" \
                    -o /dev/null
            done
        ) &
    done
    wait
    
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    TOTAL_REQUESTS=$((CONCURRENT_USERS * REQUESTS_PER_USER))
    RPS=$((TOTAL_REQUESTS / ELAPSED))
    
    echo ""
    echo "Load test completed"
    echo "Total requests: $TOTAL_REQUESTS"
    echo "Elapsed time: ${ELAPSED}s"
    echo "Requests per second: $RPS"
fi

