FROM python:3.12-slim

WORKDIR /app

COPY scheduler.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY crontab /etc/cron.d/aggregation-cron

RUN sed -i 's/\r$//' /etc/cron.d/aggregation-cron && echo >> /etc/cron.d/aggregation-cron

RUN chmod 0644 /etc/cron.d/aggregation-cron

RUN crontab /etc/cron.d/aggregation-cron

CMD ["cron", "-f"]
