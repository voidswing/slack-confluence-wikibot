# built-in
import os
from typing import Optional, List, Dict, Any

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


def post_message(slack_bot: SlackBot, message: str, ts: Optional[str] = None, is_block_kit: Optional[bool] = False, **kwargs) -> Optional[str]:
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


def get_thread_messages(channel: str, thread_ts: str) -> List[Dict[str, Any]]:
    """
    Fetch all messages in a thread
    """
    try:
        response = requests.get(
            "https://slack.com/api/conversations.replies",
            headers=SLACK_HEADERS,
            params={
                "channel": channel,
                "ts": thread_ts,
                "limit": 100  # Maximum messages to retrieve
            }
        )

        result = response.json()
        if result.get("ok", False):
            return result.get("messages", [])
        else:
            print(f"Error fetching thread messages: {result.get('error')}")
            return []
    except Exception as e:
        print(f"Exception fetching thread messages: {e}")
        return []


def format_thread_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Format thread messages for summarization
    """
    formatted_text = ""

    for message in messages:
        user = message.get("user", "Unknown")
        text = message.get("text", "")

        # Skip messages with no text
        if not text.strip():
            continue

        formatted_text += f"User {user}: {text}\n\n"

    return formatted_text

