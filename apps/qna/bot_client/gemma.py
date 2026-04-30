import json
from typing import Iterator

import requests
from django.conf import settings
from .prompts.qna_chatbot_prompt import QNA_PROMPT


def call_google(model: str, message: str) -> Iterator[str]:
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("키가 없습니다.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"

    payload = {
        "system_instruction": {
            "parts": [{"text": QNA_PROMPT}]
        },
        "contents": [
            {
                "parts": [{"text": message}]
            }
        ]
    }

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        with requests.post(url, json=payload, headers=headers, stream=True, timeout=(5, 60)) as res:
            res.raise_for_status()
            for line in res.iter_lines(decode_unicode=True):
                if not line:
                    continue
                data = line.removeprefix("data: ").strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    candidates = chunk["candidates"][0]
                    text = candidates["content"]["parts"][0].get("text")
                    if text is not None:
                        yield text

                    finish_reason = candidates.get("finishReason")
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