FROM python:3.11-alpine

WORKDIR /app

COPY . .

RUN apk add --no-cache \
  mariadb-connector-c-dev \
  gcc \
  libc-dev

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
