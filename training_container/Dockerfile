FROM python:3.12-slim

WORKDIR /app

COPY training_container/requirements.txt .

RUN pip install \
    --no-cache-dir \
    --default-timeout=1000 \
    --retries 10 \
    -r requirements.txt

COPY training_container/ ./training_container/

CMD ["python", "-u", "-m", "training_container.train"]