# Local Development Command Guide

## Read this first

This file is the project’s command roadmap. Follow the numbered commands from
top to bottom the first time you run the project.

The project is a small local cloud-style pipeline:

```text
HTTP event → Pub/Sub → MySQL → Firestore summary
                         └────→ CSV → model → prediction API
```

You are using Docker containers and local emulators, so you do not need a
paid Google Cloud account for this exercise.

### Before command 1

Install these tools first:

- Docker Desktop, and make sure it is running.
- Python 3.12 or newer.
- PowerShell.

### Important usage notes

- Run the commands from PowerShell.
- Keep this terminal open after activating `.venv`.
- `docker compose up` starts the local services.
- The HTTP ingest service is on port `8080`.
- The summary API is on port `8082`.
- The Pub/Sub and Firestore emulators are used inside Docker.
- Commands 1–13 run the event and summary part.
- Commands 14–20 run the machine-learning part.
- If a command fails, stop and read its output before continuing.

## Command index

| # | Command name | Why you use it |
|---:|---|---|
| 1 | Open the project folder | Makes sure every later path points to this project. |
| 2 | Create the virtual environment | Creates a safe, private Python environment for this project. |
| 3 | Activate the environment | Tells PowerShell to use that private Python environment. |
| 4 | Install test dependencies | Installs pytest and the libraries used by local tests. |
| 5 | Check Docker | Confirms Docker is installed and visible to PowerShell. |
| 6 | Start the local stack | Builds images and starts MySQL, emulators, workers, and APIs. |
| 7 | Check running services | Shows whether the containers started successfully. |
| 8 | Send one customer event | Tests the Phase 1 HTTP front door. |
| 9 | Read event-writer logs | Shows whether Pub/Sub delivered the event to the worker. |
| 10 | Check the MySQL row | Confirms the worker saved the event permanently. |
| 11 | Trigger aggregation | Sends the Phase 2 message that wakes the aggregation worker. |
| 12 | Read aggregation logs | Confirms the worker created customer summaries. |
| 13 | Read a customer summary | Tests the Phase 3 HTTP API. |
| 14 | Export training data | Creates one CSV row per customer for Phase 5. |
| 15 | Preview the CSV | Confirms the file exists and has the expected columns. |
| 16 | Build the training image | Packages the Phase 5 Python training program. |
| 17 | Train the model | Creates `model.joblib` and `metrics.json`. |
| 18 | Build the prediction image | Packages the Phase 6 prediction server. |
| 19 | Run the Phase 6 test | Uses the real Docker image and official `LocalModel`. |
| 20 | Run the complete test suite | Checks all project phases together. |

## The 20 commands

### 1. Open the project folder

Use this first, or whenever your terminal is currently in another folder.

```powershell
# When to use: before every project session.
Set-Location D:\Beta-project
```

### 2. Create the virtual environment

This creates a `.venv` folder. It keeps this project’s Python packages
separate from other projects on your computer. You normally do this only once.

```powershell
# When to use: the first time you prepare the project on this computer.
python -m venv .venv
```

### 3. Activate the virtual environment

After activation, `python` and `pip` point to the project environment.

```powershell
# When to use: at the beginning of each new PowerShell session.
.\.venv\Scripts\Activate.ps1
```

If PowerShell says that scripts are blocked, you can still use the environment
without activation by replacing `python` with
`.\.venv\Scripts\python.exe` in the later commands.

### 4. Install the test dependencies

This reads `requirements-dev.txt` and installs pytest, Firestore tools,
scikit-learn, and the other local development packages.

```powershell
# When to use: after creating the environment, or after dependencies change.
python -m pip install -r requirements-dev.txt
```

### 5. Check Docker

This is a quick check before starting the containers. If it fails, open Docker
Desktop and wait until it says Docker is running.

```powershell
# When to use: before starting the local cloud-style services.
docker --version
```

### 6. Start the local stack

Docker Compose builds the project images and starts MySQL, Pub/Sub emulator,
Firestore emulator, the workers, the scheduler, and the APIs.

```powershell
# When to use: at the start of a demo, or after changing Docker/source files.
docker compose up -d --build
```

### 7. Check the running services

The `STATUS` column should show the containers running or completed where
appropriate. `pubsub_init` is expected to finish after creating its topics and
subscriptions.

```powershell
# When to use: immediately after command 6, or whenever you are unsure what is running.
docker compose ps
```

### 8. Send one customer event

This sends a purchase to `POST /events/ingest`. The API validates the JSON and
publishes it to Pub/Sub. A successful response should be `202` with a queued
status.

```powershell
# When to use: to test Phase 1’s HTTP → Pub/Sub path.
$body = @{customer_id="cust_123"; event_type="purchase"; product_id="prod_456"; value=49.99; timestamp="2026-08-20T10:00:00Z"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/events/ingest -Method POST -ContentType "application/json" -Body $body
```

### 9. Read the event-writer logs

The HTTP service does not write MySQL directly. The event writer receives the
Pub/Sub message and performs the database insert.

```powershell
# When to use: after command 8, to see the asynchronous worker’s activity.
docker compose logs --tail 50 event_writer
```

### 10. Check the MySQL row

This asks the MySQL container to display recent rows. It proves that the event
passed through Pub/Sub and was saved by the worker.

```powershell
# When to use: after command 9, to confirm the event reached MySQL.
docker compose exec mysql mysql -uroot -proot -Devent_db -e "SELECT id, customer_id, event_type, value, event_timestamp FROM events ORDER BY id DESC LIMIT 5;"
```

### 11. Trigger aggregation

Normally cron runs the scheduler every two minutes. This command triggers the
same scheduler manually, so you can continue learning without waiting.

```powershell
# When to use: after a new event, when you want a summary immediately.
docker compose exec scheduler python /app/scheduler.py
```

### 12. Read aggregation logs

The aggregation worker reads MySQL, calculates totals, and writes one
Firestore document for each customer.

```powershell
# When to use: after command 11, to confirm the summary worker ran.
docker compose logs --tail 50 aggregate_worker
```

### 13. Read a customer summary

This calls the Phase 3 API. The customer ID must match the ID used in command
8. A known customer should return a summary with status `200`.

```powershell
# When to use: after aggregation has completed, to test the summary API.
curl.exe -i http://localhost:8082/customers/cust_123/summary
```

### 14. Export training data

The export job reads MySQL and creates `output/training_data.csv`. It creates
one row per customer with the six model features and the assessment label.

```powershell
# When to use: after MySQL contains enough sample events for training.
docker compose run --rm export_job
```

### 15. Preview the CSV

This displays the header and first four data rows. Confirm that the six feature
columns and `label_high_value` are present.

```powershell
# When to use: after command 14, before training the model.
Get-Content .\output\training_data.csv -TotalCount 5
```

### 16. Build the training image

This packages `training_container/train.py` and its dependencies into a Docker
image named `local-training:latest`.

```powershell
# When to use: before running the Phase 5 training job.
docker build -t local-training:latest -f training_container/Dockerfile .
```

### 17. Train the model

The first mount gives the container the CSV. The second mount gives it a place
to save the model artifacts on your computer.

```powershell
# When to use: after command 16 and whenever the training CSV changes.
docker run --rm -e TRAINING_DATA_PATH=/data/training_data.csv -e AIP_MODEL_DIR=/model -v ${PWD}/output:/data -v ${PWD}/model_output:/model local-training:latest
```

After it finishes, you should have:

```text
model_output/model.joblib
model_output/metrics.json
```

### 18. Build the prediction image

This packages the Flask/Gunicorn prediction server. The Dockerfile copies the
model into `/model/model.joblib`, where the application expects it.

```powershell
# When to use: after command 17, because the image needs the trained model.
docker build -t local-prediction:latest -f prediction_container/Dockerfile .
```

### 19. Run the Phase 6 test

This test uses Google’s official `LocalModel`. It starts the real prediction
image, checks `GET /health`, and sends a real `POST /predict` request.

```powershell
# When to use: after command 18, to prove the full prediction deployment works.
python -m pytest tests/test_phase6_prediction.py -v
```

### 20. Run the complete test suite

This runs all phase tests. Keep the Docker services running because the
Firestore-related tests use the local emulator.

```powershell
# When to use: as the final verification before sharing or presenting the project.
python -m pytest -v
```

## Optional commands

### Stop the local services

Use this when you have finished working for the day. It stops containers but
does not remove the named MySQL volume.

```powershell
# When to use: after testing, to stop the local stack.
docker compose down
```

### Start again without rebuilding

Use this when you stopped the services and did not change source code or Docker
files.

```powershell
# When to use: to start the existing images quickly.
docker compose up -d
```

## What each command proves

Commands 1–7 prepare the tools and start the local cloud-like environment.
Commands 8–10 prove that an event travels through HTTP, Pub/Sub, and MySQL.
Commands 11–13 prove that scheduled aggregation creates a readable summary.
Commands 14–17 connect MySQL to a trained model artifact.
Commands 18–20 prove that the model can be served and tested through HTTP.

## If something goes wrong

- `docker` cannot connect: start Docker Desktop and repeat command 5.
- No `202` response: inspect the ingest container with
  `docker compose logs ingest`.
- No MySQL row: inspect command 9; the API and database worker are separate.
- No summary: repeat command 11, then inspect command 12.
- CSV is empty: add events first and repeat command 14.
- Training cannot find the CSV: check that
  `output\training_data.csv` exists before command 17.
- `/health` returns `503`: check that `model_output\model.joblib` exists and
  rebuild the prediction image.
- Phase 6 cannot start Docker: make sure Docker Desktop is running before
  command 19.

## The simple interview explanation

“The client sends an event over HTTP. The ingest function validates it and
queues it in Pub/Sub, so the client does not wait for the database. A worker
reads the message and saves it in MySQL. A scheduled trigger builds Firestore
summaries for quick reads. Another job exports MySQL data to CSV, trains a
scikit-learn model, and saves `model.joblib`. Finally, a Flask/Gunicorn
container serves `/health` and `/predict`, and the official LocalModel test
proves the real local deployment.”
