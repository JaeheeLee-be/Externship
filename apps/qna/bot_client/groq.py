import json
from typing import Iterator

from django.conf import settings
from .prompts.qna_chatbot_prompt import QNA_PROMPT
import requests


def call_groq(model: str, message: str) -> Iterator[str]:
    api_key = settings.GROQ_API_KEY
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "stream": True,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": QNA_PROMPT,
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

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

                    finish_reason = choice.get("finish_reason")
                    if finish_reason:
                        yield finish_reason

                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    except requests.HTTPError as e:
        raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text}")
    except requests.ConnectionError:
        raise RuntimeError("서버에 연결할 수 없습니다.")
    except requests.Timeout:
        raise RuntimeError("요청 시간이 초과되었습니다.")