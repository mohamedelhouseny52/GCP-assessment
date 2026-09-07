# GCP-Style Backend Assessment Project

This project implements a fully local version of a GCP-style backend and machine-learning pipeline.

It uses Docker, MySQL, the Google Pub/Sub emulator, the Firestore emulator, Python, pandas, scikit-learn, and the Vertex AI local prediction tools.

The project is divided into six phases:

1. Event ingestion
2. Scheduled customer aggregation
3. Customer summary API
4. Training data export
5. Model training
6. Prediction serving

Everything runs locally. No GCP account is required.

---

## Requirements

The main requirements are:

- Docker Desktop
- Docker Compose
- Python
- pytest

For Phase 6 local Vertex validation:

```powershell
pip install "google-cloud-aiplatform[prediction]>=1.16.0"
```

The project was tested locally with:

```text
google-cloud-aiplatform 2.1.0
```

---

# Phase 1 — Event Capture

Phase 1 exposes an HTTP endpoint that accepts customer events.

The ingest function validates the event and publishes it to the local Pub/Sub emulator. The event writer consumes the Pub/Sub message and stores the event in MySQL.

Supported event types:

```text
view
add_to_cart
purchase
```

A valid event contains:

```json
{
  "customer_id": "cust_123",
  "event_type": "purchase",
  "product_id": "prod_456",
  "value": 49.99,
  "timestamp": "2026-07-13T10:15:00Z"
}
```

`value` is required only for purchase events.

## Run Phase 1

Start the local services:

```powershell
docker compose up -d --build
```

Send a valid event:

```powershell
curl.exe -i -X POST http://localhost:8080/events/ingest -H "Content-Type: application/json" -d "{\"customer_id\":\"cust_123\",\"event_type\":\"purchase\",\"product_id\":\"prod_456\",\"value\":49.99,\"timestamp\":\"2026-07-13T10:15:00Z\"}"
```

A successful request returns HTTP `202` with:

```json
{
  "status": "queued"
}
```

The event can then be verified in MySQL.

---

# Phase 2 — Scheduled Aggregation

Phase 2 calculates customer statistics from the events stored in MySQL.

The scheduler publishes an aggregation trigger to Pub/Sub every two minutes during local testing.

The aggregation worker reads all historical events for each customer and writes one aggregate document per customer to Firestore.

## Aggregation Logic

This project uses an **all-time aggregation window**.

Every aggregation run recalculates the customer's statistics from all events currently stored in MySQL.

This makes the aggregation idempotent. Running it multiple times does not duplicate totals.

Each Firestore document contains fields such as:

```json
{
  "customer_id": "cust_123",
  "total_events": 42,
  "total_value": 310.50,
  "purchase_count": 3,
  "last_event_at": "2026-07-13T09:50:00Z",
  "updated_at": "2026-07-13T10:00:00Z"
}
```

To manually trigger aggregation without waiting for the scheduler:

```powershell
docker compose exec scheduler python /app/scheduler.py
```

---

# Phase 3 — Customer Summary API

Phase 3 exposes the customer aggregate stored in Firestore.

Endpoint:

```text
GET /customers/{customer_id}/summary
```

## 200 — Known Customer

```powershell
curl.exe -i http://localhost:8082/customers/cust_123/summary
```

Expected result:

```text
HTTP 200
```

with the customer aggregate as JSON.

## 404 — Unknown Customer

```powershell
curl.exe -i http://localhost:8082/customers/unknown_customer/summary
```

Expected response:

```json
{
  "error": "customer not found"
}
```

## 503 — Firestore Unavailable

If the Firestore emulator is unavailable, the endpoint returns HTTP `503`.

Stop Firestore:

```powershell
docker compose stop firestore
```

Call the endpoint:

```powershell
curl.exe -i http://localhost:8082/customers/cust_123/summary
```

Expected response:

```json
{
  "error": "service unavailable"
}
```

Restart Firestore afterward:

```powershell
docker compose start firestore
```

## 500 — Malformed Firestore Document

If a customer document exists but is missing required aggregate fields, the API returns HTTP `500`.

Expected response:

```json
{
  "error": "internal server error"
}
```

This case is covered by the Phase 3 automated tests.

---

# Phase 4 — Training Data Export

Phase 4 generates:

```text
output/training_data.csv
```

The export job reads all historical customer events from MySQL and creates one row per customer.

Run it with:

```powershell
docker compose run --rm export_job
```

## Dataset Schema

| Column | Type | Description |
|---|---|---|
| `customer_id` | string | Unique customer identifier |
| `total_events` | int | Total number of events |
| `total_value` | float | Sum of values from purchase events |
| `purchase_count` | int | Number of purchase events |
| `view_count` | int | Number of view events |
| `cart_count` | int | Number of add-to-cart events |
| `days_since_last_event` | int | Days between the customer's latest event and export time |
| `label_high_value` | int | Training target, either 0 or 1 |

The label is deterministic:

```text
label_high_value = 1 if total_value > 200
label_high_value = 0 otherwise
```

Customers with no events do not appear in the exported dataset.

A sample `training_data.csv` is included in the repository for inspection.

---

# Phase 5 — Model Training

Phase 5 trains a local scikit-learn classification model using the CSV produced in Phase 4.

The implementation uses:

- pandas
- train/test split
- StandardScaler
- LogisticRegression

The output directory contains:

```text
model.joblib
metrics.json
```

Build the training image:

```powershell
docker build -t local-training -f training_container/Dockerfile .
```

The exact command used to run training locally is:

```powershell
docker run --rm -e TRAINING_DATA_PATH=/data/training_data.csv -e AIP_MODEL_DIR=/model -v ${PWD}/output:/data -v ${PWD}/model_output:/model local-training
```

`TRAINING_DATA_PATH` tells the container where the CSV is located.

`AIP_MODEL_DIR` tells the training code where to write the model artifacts.

After training:

```powershell
Get-Content .\model_output\metrics.json
```

The generated files are:

```text
model_output/model.joblib
model_output/metrics.json
```

---

# Phase 6 — Prediction Serving

Phase 6 serves the trained model using a Vertex-style prediction container.

The container implements:

```text
GET /health
POST /predict
```

`GET /health` returns HTTP `200` only after the model has been loaded successfully.

## Prediction Input

```json
{
  "instances": [
    {
      "total_events": 12,
      "total_value": 250.0,
      "purchase_count": 2,
      "view_count": 8,
      "cart_count": 2,
      "days_since_last_event": 3
    }
  ]
}
```

## Prediction Output

```json
{
  "predictions": [
    {
      "label_high_value": 1,
      "probability": 0.87
    }
  ]
}
```

Build the prediction image after Phase 5 training:

```powershell
docker build -t local-prediction -f prediction_container/Dockerfile .
```

The current local Docker image copies the generated model into:

```text
/model/model.joblib
```

## Vertex LocalModel Validation

The Phase 6 test validates the serving container using the official Vertex AI `LocalModel` tool.

The exact Python code used is:

```python
import json

from google.cloud.aiplatform.prediction import LocalModel


local_model = LocalModel(
    serving_container_image_uri="local-prediction:latest",
    serving_container_predict_route="/predict",
    serving_container_health_route="/health",
    serving_container_ports=[8080],
)

with local_model.deploy_to_local_endpoint(
    host_port="8084",
    container_ready_timeout=120,
) as endpoint:

    health_response = endpoint.run_health_check()

    request_body = json.dumps({
        "instances": [
            {
                "total_events": 20,
                "total_value": 500.0,
                "purchase_count": 4,
                "view_count": 10,
                "cart_count": 3,
                "days_since_last_event": 2
            }
        ]
    })

    predict_response = endpoint.predict(
        request=request_body,
        headers={
            "Content-Type": "application/json"
        },
    )
```

Run the Phase 6 tests with:

```powershell
python -m pytest tests/test_phase6_prediction.py -v
```

Expected result:

```text
5 passed
```

---

# Running the Complete Project

Start the backend services:

```powershell
docker compose up -d --build
```

Check them:

```powershell
docker compose ps
```

Main local endpoints:

| Component | Address |
|---|---|
| Event ingest | `http://localhost:8080` |
| Customer summary API | `http://localhost:8082` |
| Firestore emulator | `localhost:8081` |
| Pub/Sub emulator | `localhost:8085` |
| MySQL | `localhost:3306` |

The normal full run is:

1. Submit a customer event.
2. Confirm it is written to MySQL.
3. Trigger or wait for customer aggregation.
4. Read the customer summary from the API.
5. Run the export job.
6. Run model training.
7. Rebuild the prediction container with the newly generated model.
8. Validate prediction serving using `LocalModel`.

---

# End-to-End Smoke Test

The final integration test uses one customer through the complete pipeline.

Example customer:

```text
e2e_customer_001
```

Start all services:

```powershell
docker compose up -d --build
```

Submit a purchase event:

```powershell
$body = @{event_type="purchase"; customer_id="e2e_customer_001"; product_id="e2e_product_001"; timestamp="2026-09-08T00:30:00Z"; value=350} | ConvertTo-Json; Invoke-RestMethod -Uri http://localhost:8080/events/ingest -Method POST -ContentType "application/json" -Body $body
```

Confirm the event in MySQL:

```powershell
docker compose exec mysql mysql -uroot -proot event_db -e "SELECT id,customer_id,event_type,product_id,value,event_timestamp FROM events WHERE customer_id='e2e_customer_001';"
```

Trigger aggregation:

```powershell
docker compose exec scheduler python /app/scheduler.py
```

Check the summary:

```powershell
curl.exe -i http://localhost:8082/customers/e2e_customer_001/summary
```

Run the export:

```powershell
docker compose run --rm export_job
```

Confirm the customer exists in the exported dataset:

```powershell
Select-String -Path .\output\training_data.csv -Pattern "e2e_customer_001"
```

Build the training image:

```powershell
docker build -t local-training -f training_container/Dockerfile .
```

Run training:

```powershell
docker run --rm -e TRAINING_DATA_PATH=/data/training_data.csv -e AIP_MODEL_DIR=/model -v ${PWD}/output:/data -v ${PWD}/model_output:/model local-training
```

Confirm the model artifact:

```powershell
Get-Item .\model_output\model.joblib
```

Confirm the metrics:

```powershell
Get-Content .\model_output\metrics.json
```

Rebuild the prediction image using the newly trained model:

```powershell
docker build -t local-prediction -f prediction_container/Dockerfile .
```

Run the Phase 6 validation:

```powershell
python -m pytest tests/test_phase6_prediction.py -v
```

Finally, run the complete test suite:

```powershell
python -m pytest -v
```

Expected result:

```text
23 passed
```

---

# Tests

Run every automated test with:

```powershell
python -m pytest -v
```

The project contains tests for all six phases.

---

# Local to Real GCP Mapping

| Local Component | GCP Equivalent |
|---|---|
| Functions Framework HTTP function | Cloud Functions Gen2 |
| Pub/Sub emulator | Cloud Pub/Sub |
| Cron scheduler container | Cloud Scheduler |
| MySQL Docker container | Cloud SQL for MySQL |
| Firestore emulator | Firestore |
| Export Docker job | Cloud Run Job |
| Training container | Vertex AI custom training |
| Prediction container + LocalModel | Vertex AI Model + Endpoint |