FROM python:3.12-slim

WORKDIR /app

COPY aggregate_function/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY aggregate_function/ ./aggregate_function/
COPY MySql/ ./MySql/

CMD ["python", "-u", "-m", "aggregate_function.worker"]