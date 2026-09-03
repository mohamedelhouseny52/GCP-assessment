FROM python:3.12-slim

WORKDIR /app

COPY scheduler.py .

RUN pip install google-cloud-pubsub

RUN apt-get update && apt-get install -y cron

COPY crontab /etc/cron.d/aggregation-cron

RUN sed -i 's/\r$//' /etc/cron.d/aggregation-cron && echo >> /etc/cron.d/aggregation-cron

RUN chmod 0644 /etc/cron.d/aggregation-cron

RUN crontab /etc/cron.d/aggregation-cron

CMD ["cron", "-f"]