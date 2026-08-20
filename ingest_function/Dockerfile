FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ingest_function/ ./ingest_function/
COPY MySql/ ./MySql/

CMD ["functions-framework", "--target=ingest_event", "--debug", "--port=8080"]