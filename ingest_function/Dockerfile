FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --default-timeout=1000 \
    --retries 10 \
    -r requirements.txt

COPY ingest_function/main.py ./main.py

EXPOSE 8080

CMD ["functions-framework", "--target=ingest_event", "--port=8080"]