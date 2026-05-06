import json
from typing import Any, Iterator

import requests

from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_groq(payload: dict[str, Any], key: str) -> Iterator[str]:
    url = GROQ_API_URL
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}

    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=(5, 60)) as res:
            res.raise_for_status()
            for line in res.iter_lines(decode_unicode=True):
                if not line:
                    continue
                data = line.removeprefix("data: ").strip()
                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                    choice = chunk["choices"][0]
                    content = choice["delta"].get("content")
                    if content is not None:
                        yield content

                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    except (requests.HTTPError, requests.ConnectionError):
        raise GroqAPIError()
    except requests.Timeout:
        raise GroqTimeoutError()


def call_groq_once(payload: dict[str, Any], key: str) -> str:
    url = GROQ_API_URL
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    try:
        with requests.post(url, headers=headers, json=payload, timeout=(5, 60)) as res:
            res.raise_for_status()
            return str(res.json()["choices"][0]["message"]["content"])

    except (json.JSONDecodeError, KeyError, IndexError, requests.HTTPError, requests.ConnectionError):
        raise GroqAPIError()
    except requests.Timeout:
        raise GroqTimeoutError()
