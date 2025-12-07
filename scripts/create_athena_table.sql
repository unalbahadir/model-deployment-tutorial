-- Create Athena table for storing predictions
-- This table will query data stored in S3 in Parquet format
-- Update the LOCATION with your S3 bucket name

CREATE EXTERNAL TABLE IF NOT EXISTS model_predictions (
    user_id bigint,
    movie_id bigint,
    age int,
    gender string,
    prediction double,
    prediction_class int,
    model_version string,
    inference_time_ms double,
    timestamp timestamp
)
PARTITIONED BY (
    year int,
    month int,
    day int,
    hour int
)
STORED AS PARQUET
LOCATION 's3://your-bucket-name/predictions/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.year.type' = 'integer',
    'projection.year.range' = '2024,2030',
    'projection.year.format' = 'yyyy',
    'projection.month.type' = 'integer',
    'projection.month.range' = '1,12',
    'projection.month.format' = 'MM',
    'projection.day.type' = 'integer',
    'projection.day.range' = '1,31',
    'projection.day.format' = 'dd',
    'projection.hour.type' = 'integer',
    'projection.hour.range' = '0,23',
    'projection.hour.format' = 'HH',
    'storage.location.template' = 's3://your-bucket-name/predictions/${year}/${month}/${day}/${hour}'
);

-- Example queries:
-- 
-- Get recent predictions:
-- SELECT * FROM model_predictions 
-- WHERE year = 2024 AND month = 12 
-- ORDER BY timestamp DESC 
-- LIMIT 100;
--
-- Get average prediction by user:
-- SELECT user_id, AVG(prediction) as avg_prediction, COUNT(*) as prediction_count 
-- FROM model_predictions 
-- WHERE year = 2024 AND month = 12 
-- GROUP BY user_id 
-- ORDER BY prediction_count DESC 
-- LIMIT 10;
--
-- Get predictions for a specific user:
-- SELECT * FROM model_predictions 
-- WHERE user_id = 259 
-- AND year = 2024 AND month = 12
-- ORDER BY timestamp DESC;

