# Confluence 위키봇 프로젝트

Confluence의 데이터를 활용하여 슬랙에서 위키 정보를 제공하는 봇

## 🚀 시작하기

### 1. 환경 변수 설정

프로젝트 루트에 있는 `.env.sample` 파일을 복사하여 `.env` 파일을 생성하고, 값을 변경합니다.

```bash
CONFLUENCE_URL=CHANGE_ME
CONFLUENCE_USERNAME=CHANGE_ME
CONFLUENCE_API_TOKEN=CHANGE_ME
SPACE_KEY=CHANGE_ME
OPENAI_API_KEY=CHANGE_ME
OPENAI_EMBEDDING_MODEL=CHANGE_ME
SLACK_TOKEN=CHANGE_ME
```

### 2. 기존 컨테이너 중지 및 삭제

코드 변경 후 다시 실행하기 위해 기존 컨테이너를 중지하고 삭제합니다.

```bash
# 실행 중인 컨테이너 중지
docker stop wiki-container

# 컨테이너 삭제
docker rm wiki-container
```

### 3. Docker 이미지 빌드 및 컨테이너 실행

다음 명령어로 Docker 이미지를 빌드하고 컨테이너를 실행하세요.

```bash
docker build -t wiki-fastapi-dev .
docker run -d -p 8000:8000 -v $(pwd):/app --name wiki-container wiki-fastapi-dev
```

### 4. Confluence 데이터 벡터DB에 학습시키기

실행 중인 Docker 컨테이너 내부에서 다음 명령어를 실행하여 Confluence 데이터를 벡터DB에 학습시킵니다.

```bash
docker exec -it wiki-container python -m src.ingestion.run --all
```

### 5. Slack Events API 활성화

슬랙에서 봇이 메시지에 반응하도록 하려면 [Slack Events API](https://api.slack.com/apis/events-api)를 활성화하세요.

## 📚 사용 방법

### 위키 검색

슬랙 채널이나 DM에서 `위키/` 명령어를 사용하여 Confluence 위키를 검색할 수 있습니다:

```
위키/프로젝트 설정 방법
```

### 스레드 요약

슬랙 스레드 내에서 `요약/` 명령어를 사용하여 해당 스레드의 내용을 요약할 수 있습니다:

```
요약/
```

스레드 내용을 분석하여 다음과 같은 형식으로 요약을 제공합니다:
1. 스레드 전체 주제
2. 주요 논의 사항 (3-5개 불릿 포인트)
3. 결론 또는 다음 단계 (있는 경우)
