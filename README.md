# GCP-Style Backend Assessment Project

Local backend project built with Docker, MySQL, Pub/Sub emulator, and Firestore emulator.

The project is split into phases. Each phase adds a new part to the backend system.

---

## Project Flow

```text
Phase 1
HTTP POST
→ Ingest Function
→ Pub/Sub
→ Event Writer
→ MySQL

Phase 2
Cron Scheduler
→ Pub/Sub Trigger
→ Aggregate Worker
→ MySQL
→ Firestore

Phase 3
HTTP GET
→ Summary API
→ Firestore
→ JSON Response

# Phase 4 — Training Data Export

Phase 4 prepares the historical MySQL event data for machine learning.

Flow:

```text
MySQL
→ Export Job
→ training_data.csv


# Phase 5 — Model Training

Phase 5 trains a local machine learning model using the dataset generated in Phase 4.

Flow:

```text
training_data.csv
→ pandas
→ train/test split
→ Logistic Regression
→ model.joblib
→ metrics.json