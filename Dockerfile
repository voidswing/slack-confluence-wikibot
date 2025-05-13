FROM python:3.12-slim

# 필요한 패키지 및 cron 설치
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    sqlite3 \
    cron

# cron 로그 파일 생성
RUN touch /var/log/cron.log

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 크론 작업 설정
COPY cronjob /etc/cron.d/confluence-cron
RUN chmod 0644 /etc/cron.d/confluence-cron


CMD cron && uvicorn src.main:app --host 0.0.0.0 --port 8000
# CMD cron && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
