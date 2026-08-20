<<<<<<< HEAD
# Phase 1 — Event Capture Pipeline

This project implements Phase 1 of an event-driven backend pipeline.

A client sends an event through an HTTP endpoint. The event is validated and published to Pub/Sub. An Event Writer consumes the message and stores the validated event in MySQL.

The project can be tested locally using Docker and the Google Cloud Pub/Sub emulator, so a Google Cloud account is not required for local testing.

---

## Architecture

The event flow is:

```text
HTTP Request
     ↓
Ingest Function
     ↓
Pub/Sub
     ↓
Event Writer
     ↓
MySQL
```

### Components

**Ingest Function**

Receives HTTP event requests, validates the input, and publishes valid events to the `raw-events` Pub/Sub topic.

**Pub/Sub**

Provides asynchronous communication between the ingest function and the Event Writer.

For local testing, the Google Cloud Pub/Sub emulator is used.

**Event Writer**

Consumes events from the `event-writer-sub` subscription, validates the received event, and writes it to MySQL.

**MySQL**

Stores the final event records in the `events` table.

---

## Supported Event Types

The following event types are currently supported:

- `view`
- `add_to_cart`
- `purchase`

Purchase events also require a numeric `value`.

---

## Example Event

```json
{
  "event_type": "purchase",
  "customer_id": "cust_999",
  "product_id": "prod_999",
  "timestamp": "2026-08-20T19:30:00Z",
  "value": 99.99
}
```

---

## Local Requirements

For the simplest local setup:

- Docker Desktop
- Git

No Google Cloud account is required when using the local Pub/Sub emulator.

---

## Quick Start

Clone the repository and enter the project directory.

Then start the services:

```bash
docker compose up --build
```

Docker is used to provide the local infrastructure required by the project, including MySQL and the Pub/Sub emulator.

---

## Testing the API

Once the services are running, send a `POST` request to the ingest endpoint.

Endpoint:

```text
http://localhost:8080
```

Example request body:

```json
{
  "event_type": "purchase",
  "customer_id": "cust_999",
  "product_id": "prod_999",
  "timestamp": "2026-08-20T19:30:00Z",
  "value": 99.99
}
```

A successfully accepted event returns:

```json
{
  "status": "queued"
}
```

with HTTP status:

```text
202 Accepted
```

The `202` response means that Pub/Sub accepted the event for asynchronous processing.

---

## Validation

The ingest service validates:

- Required fields
- Supported event types
- Customer ID
- Product ID
- Timestamp format
- Purchase value

Invalid requests return an appropriate `4xx` response instead of being published.

The Event Writer performs validation again before writing the event to MySQL.

---

## Database

Events are stored in the MySQL `events` table.

The stored data includes:

- Event ID
- Customer ID
- Event type
- Product ID
- Value
- Event timestamp
- Creation timestamp

---

## Project Structure

```text
.
├── ingest_function/
│   └── main.py
│
├── event_writer/
│   ├── __init__.py
│   ├── event_writer.py
│   └── subscriber.py
│
├── MySql/
│   ├── __init__.py
│   ├── MySql.py
│   └── init.sql
│
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Python Dependencies

The main Python dependencies are:

- Functions Framework
- Flask
- Google Cloud Pub/Sub client
- MySQL Connector for Python

They are listed in `requirements.txt`.

---

## Local Development

The local environment uses:

```text
MySQL:          localhost:3306
HTTP API:       localhost:8080
Pub/Sub:        localhost:8085
```

The Pub/Sub emulator uses:

```text
Project:        local-project
Topic:          raw-events
Subscription:   event-writer-sub
```

---

## Notes

This repository focuses on the event capture pipeline and asynchronous processing flow.

The local Pub/Sub emulator allows the architecture to be demonstrated without requiring access to a live Google Cloud project.

**Phase 1 Status**: Complete ✓
- Event ingestion with validation
- Pub/Sub decoupling
- Event persistence in MySQL
- Comprehensive unit tests
- Docker infrastructure
