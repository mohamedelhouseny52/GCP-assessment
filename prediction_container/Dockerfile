FROM python:3.12-slim

WORKDIR /app

COPY prediction_container/requirements.txt .

RUN pip install \
    --no-cache-dir \
    --default-timeout=1000 \
    --retries 10 \
    -r requirements.txt

COPY prediction_container/ ./prediction_container/

COPY model_output/model.joblib /model/model.joblib

ENV MODEL_PATH=/model/model.joblib

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "prediction_container.app:app"]