# built-in
import os
from typing import Optional

# pydantic
from pydantic import BaseModel

# requests
import requests


SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_HEADERS = {
    "Content-type": "application/json; charset=utf8",
    "Authorization": f"Bearer {SLACK_TOKEN}",
}


class SlackBot(BaseModel):
    channel: str
    username: str
    emoji: str


def post_message(slack_bot: SlackBot, message: str, ts: Optional[int] = None, is_block_kit: Optional[bool] = False, **kwargs) -> Optional[int]:
    payload = {**kwargs}
    payload["channel"] = slack_bot.channel
    payload["username"] = slack_bot.username
    payload["icon_emoji"] = slack_bot.emoji

    if is_block_kit:
        payload["blocks"] = message
    else:
        payload["text"] = message

    if ts is not None:
        payload["thread_ts"] = ts


    try:
        response = requests.post("https://slack.com/api/chat.postMessage", headers=SLACK_HEADERS, json=payload)
        return response.json().get("ts")
    except Exception as e:
        print(e)
        return None

