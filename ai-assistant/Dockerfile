FROM python:3.12-alpine

RUN apk add --no-cache curl gcc musl-dev postgresql-dev

WORKDIR /app

COPY shared/ /app/shared/
COPY ai-assistant/ .

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=180

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --retries=10 --default-timeout=180 -r requirements.txt && \
    pip install --retries=10 --default-timeout=180 psycopg2-binary

EXPOSE 8007

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
