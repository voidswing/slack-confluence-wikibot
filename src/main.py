from fastapi import FastAPI
from src.routes import slack

app = FastAPI()

app.include_router(slack.router, prefix="/slack", tags=["Slack"])

