FROM python:3.12-slim

WORKDIR /app

COPY export_job/requirements.txt .

RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY export_job/ ./export_job/
COPY MySql/ ./MySql/

CMD ["python", "-u", "-m", "export_job.main"]