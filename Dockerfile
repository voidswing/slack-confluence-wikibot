FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libreadline-dev \
    zlib1g-dev

RUN apt-get install -y sqlite3

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

