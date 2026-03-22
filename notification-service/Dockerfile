FROM python:3.12-alpine

RUN apk add --no-cache curl gcc musl-dev postgresql-dev

WORKDIR /app

COPY shared/ /app/shared/
COPY notification-service/ .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary

EXPOSE 8006

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
