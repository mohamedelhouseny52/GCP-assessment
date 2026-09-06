FROM python:3.12-slim

WORKDIR /app

COPY summary_api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY summary_api/ ./summary_api/

CMD ["functions-framework", "--target=summary_api", "--source=summary_api/main.py", "--port=8080"]