# built-in
import os
from typing import Any, Dict, List

# fastapi
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request, BackgroundTasks

# python-dotenv
from dotenv import load_dotenv

# openai
import openai
from openai import AsyncOpenAI

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
SUMMARY_COMMAND_PREFIX = "요약/"


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
    print(text)

    channel = event["channel"]
    ts = event.get("thread_ts") or event.get("ts")

    if text.startswith(WIKI_COMMAND_PREFIX):
        await handle_wiki_command(text, channel, ts)
    elif text.startswith(SUMMARY_COMMAND_PREFIX):
        await handle_summary_command(channel, ts)


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


async def handle_summary_command(channel: str, thread_ts: str) -> None:
    """
    Summarize a Slack thread and post the summary back to the thread
    """
    # Get the thread messages
    messages = slacks.get_thread_messages(channel, thread_ts)

    # Skip if there are no messages
    if not messages or len(messages) <= 1:
        slack_bot = slacks.SlackBot(
            channel=channel,
            username="요약봇",
            emoji=":memo:"
        )
        slacks.post_message(
            slack_bot=slack_bot,
            message="요약할 메시지가 충분하지 않습니다.",
            ts=thread_ts
        )
        return

    # Format the messages for the model
    formatted_messages = slacks.format_thread_messages(messages)

    # Generate summary with OpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 슬랙 스레드 내용을 요약하는 도우미입니다. "
                    "주어진 슬랙 스레드의 대화 내용을 간결하게 요약해주세요. "
                    "요약은 다음 형식을 따라야 합니다:\n\n"
                    "1. 스레드 전체 주제 또는 목적\n"
                    "2. 주요 논의 사항 (불릿 포인트로 3-5개)\n"
                    "3. 결론 또는 다음 단계 (있는 경우)\n\n"
                    "매우 중요: 슬랙에서 볼드체는 별표(*) 한 개만 사용합니다. 절대 별표 두 개(**)를 사용하지 마세요.\n"
                    "예시: *이것은 볼드체입니다* (O), **이것은 잘못된 형식입니다** (X)\n"
                    "`코드`, ```코드 블록```등을 적절히 사용해 요약을 보기 좋게 작성하세요."
                )
            },
            {
                "role": "user",
                "content": f"다음 슬랙 스레드 내용을 요약해주세요:\n\n{formatted_messages}"
            }
        ],
        temperature=0.3,
    )

    summary = completion.choices[0].message.content.strip()

    # Post the summary back to the thread
    slack_bot = slacks.SlackBot(
        channel=channel,
        username="요약봇",
        emoji=":memo:"
    )

    summary_message = f"*스레드 요약*\n\n{summary}"
    slacks.post_message(slack_bot=slack_bot, message=summary_message, ts=thread_ts)
