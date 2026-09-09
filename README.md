# Beginner GCP-style backend project

This project is a small local version of a Google Cloud data pipeline. It is
split into six phases, but the story is simple:

1. An HTTP function receives an event.
2. Pub/Sub carries the event to a worker.
3. The worker stores it in MySQL.
4. A scheduled message starts aggregation.
5. Aggregation writes customer summaries to Firestore.
6. A CSV is used to train a model, and another container serves predictions.

Everything runs in Docker. The project uses emulators, so a GCP account is not
needed.

## What to install

- Docker Desktop
- Python 3.12 or newer

Create a virtual environment and install the host-side test tools:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Folders

| Folder | Simple job |
|---|---|
| `ingest_function` | Validate HTTP events and publish `raw-events` |
| `event_writer` | Read `raw-events` and insert MySQL rows |
| `MySql` | One small database connection/insert helper |
| `scheduler` | Cron publishes `run-aggregation` every two minutes |
| `aggregate_function` | Read MySQL and write Firestore summaries |
| `summary_api` | Return one customer summary over HTTP |
| `export_job` | Create `output/training_data.csv` |
| `training_container` | Train and save `model.joblib` and `metrics.json` |
| `prediction_container` | Serve `/health` and `/predict` |
| `tests` | Demonstrate the required behavior |

## Phase 1: receive and store events

The endpoint is:

```text
POST http://localhost:8080/events/ingest
```

Valid event types are `view`, `add_to_cart`, and `purchase`. A purchase must
include a numeric `value`; the other event types do not need one.

Start the local services:

```powershell
docker compose up -d --build
```

Send an event:

```powershell
$body = @{customer_id="cust_123"; event_type="purchase"; product_id="prod_456"; value=49.99; timestamp="2026-08-20T10:00:00Z"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/events/ingest -Method POST -ContentType "application/json" -Body $body
```

The successful response is HTTP `202`:

```json
{"status":"queued"}
```

The ingest function does not write MySQL directly. It publishes to Pub/Sub;
the event writer receives the message and writes the row.

## Phase 2: aggregate customers

The scheduler sends a small trigger message to `run-aggregation`. You can wait
for cron or trigger it now:

```powershell
docker compose exec scheduler python /app/scheduler.py
```

The aggregation worker reads all events and replaces one Firestore document:

```text
customer_aggregates/{customer_id}
```

The document contains `customer_id`, `total_events`, `total_value`,
`purchase_count`, `last_event_at`, and `updated_at`. Because it recalculates
from all events and replaces the document, running it twice does not double
the totals.

## Phase 3: read a summary

```powershell
curl.exe http://localhost:8082/customers/cust_123/summary
```

The API returns:

- `200` when the customer document exists and is valid;
- `404` when the customer is unknown;
- `503` when Firestore cannot be reached;
- `500` when the document exists but is missing required fields.

## Phase 4: export training data

Create one CSV row per customer:

```powershell
docker compose run --rm export_job
```

The file is `output/training_data.csv` with these exact columns:

```text
customer_id,total_events,total_value,purchase_count,view_count,cart_count,days_since_last_event,label_high_value
```

The label rule is deliberately easy:

```text
label_high_value = 1 when total_value > 200
label_high_value = 0 otherwise
```

## Phase 5: train the model

Build the training image:

```powershell
docker build -t local-training -f training_container/Dockerfile .
```

Run it with the CSV as input and `model_output` as output:

```powershell
docker run --rm -e TRAINING_DATA_PATH=/data/training_data.csv -e AIP_MODEL_DIR=/model -v ${PWD}/output:/data -v ${PWD}/model_output:/model local-training
```

The command creates:

```text
model_output/model.joblib
model_output/metrics.json
```

## Phase 6: serve predictions

Build the prediction image after Phase 5:

```powershell
docker build -t local-prediction:latest -f prediction_container/Dockerfile .
```

The container has the Vertex-style contract:

```text
GET  /health
POST /predict
```

Health returns `200` only when `model.joblib` loaded successfully. Prediction
accepts six numeric features:

```json
{
  "instances": [{
    "total_events": 20,
    "total_value": 500.0,
    "purchase_count": 4,
    "view_count": 10,
    "cart_count": 3,
    "days_since_last_event": 2
  }]
}
```

The response is:

```json
{"predictions":[{"label_high_value":1,"probability":0.87}]}
```

The Phase 6 deployment test uses the official Vertex AI `LocalModel`:

```powershell
python -m pytest tests/test_phase6_prediction.py -v
```

It starts `local-prediction:latest`, checks `/health`, and sends a real
prediction request. It does not mock or bypass `LocalModel`.

## Tests

The Phase 2, 3, and 4 tests that use Firestore need the local services running.
Run the complete suite with:

```powershell
python -m pytest -v
```

The tests cover all six phases, including the required Phase 1 cases:

- valid ingest returns `202`;
- missing customer ID returns `400`;
- invalid event type returns `400`;
- purchase without value returns `400`;
- the event writer inserts a row;
- malformed Pub/Sub data is handled safely.

## Local services and their cloud equivalents

| Local project part | GCP idea |
|---|---|
| Functions Framework | Cloud Functions HTTP function |
| Pub/Sub emulator | Pub/Sub |
| Cron container | Cloud Scheduler |
| MySQL container | Cloud SQL for MySQL |
| Firestore emulator | Firestore |
| Export container | Cloud Run Job |
| Training container | Vertex AI custom training |
| Prediction container + `LocalModel` | Vertex AI model endpoint |
