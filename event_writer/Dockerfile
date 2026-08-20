FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY event_writer/ ./event_writer/
COPY MySql/ ./MySql/

CMD ["python", "-m", "event_writer.subscriber"]