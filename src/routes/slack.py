# built-in
import os
from typing import Any, Dict

# fastapi
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request, BackgroundTasks

# python-dotenv
from dotenv import load_dotenv

# openai
import openai

# query
from query.query import query_confluence

# utils
from utils import slacks

# 환경변수 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
SPACE_KEY = os.getenv("SPACE_KEY")

router = APIRouter()

BOT_MESSAGE_SUBTYPE = "bot_message"
VALID_CHANNEL_TYPES = {"im", "channel"}
WIKI_COMMAND_PREFIX = "위키/"


@router.post("/events")
async def slack_event_handler(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    payload = await request.json()

    if "challenge" in payload:
        return JSONResponse(content={"challenge": payload["challenge"]})

    background_tasks.add_task(process_event, payload)
    return JSONResponse(content={"status": "ok"}, headers={"x-slack-no-retry": "1"})


async def process_event(payload: Dict[str, Any]) -> None:
    event = payload.get("event", {})

    if not is_valid_event(event):
        return

    text = event["text"].strip()

    if text.startswith(WIKI_COMMAND_PREFIX):
        channel = event["channel"]
        ts = event.get("thread_ts") or event.get("ts")
        await handle_wiki_command(text, channel, ts)


def is_valid_event(event: Dict[str, Any]) -> bool:
    if event.get("type") != "message":
        return False

    if event.get("channel_type") not in VALID_CHANNEL_TYPES:
        return False

    message = event.get("message", {})
    if message.get("subtype") == BOT_MESSAGE_SUBTYPE:
        return False

    return "text" in event


async def handle_wiki_command(text: str, channel: str, ts: str) -> None:
    search_query = text[len(WIKI_COMMAND_PREFIX):].strip()
    result = await query_confluence(search_query)

    slack_bot = slacks.SlackBot(
        channel=channel,
        username="위키",
        emoji=":robot_face:"
    )

    slacks.post_message(slack_bot=slack_bot, message=result, ts=ts)
