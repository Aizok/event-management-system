FROM python:3.12-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY shared/ /app/shared/
COPY user-service/ .
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
