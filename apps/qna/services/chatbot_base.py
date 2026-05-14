from dataclasses import asdict
from datetime import datetime
from typing import Iterator

from django.conf import settings

from apps.qna.chatbot import call_groq
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.dtos import GroqPayload, Message
from apps.qna.exceptions import ExternalAPIException, ExternalAPITimeoutException
from apps.qna.redis import CacheRepository


class ChatbotBaseService:
    GROQ_TIMEOUT = (5, 60)

    @staticmethod
    def _store_history(key: str, history: list[Message] | None, messages: list[Message], ttl: int) -> None:
        CacheRepository.save_history(
            key=key,
            history=[asdict(m) for m in ((history or []) + messages)],
            ttl=ttl,
        )

    @staticmethod
    def _build_messages(message: str, answer: str) -> list[Message]:
        return [
            Message(role="user", content=message),
            Message(role="assistant", content=answer, created_at=datetime.now().isoformat()),
        ]

    @staticmethod
    def _stream_and_save_chat(
        key: str, history: list[Message] | None, message: str, payload: GroqPayload, ttl: int
    ) -> Iterator[str]:
        try:
            answer = ""
            for chunk in call_groq((payload.api()), settings.GROQ_API_KEY, timeout=ChatbotBaseService.GROQ_TIMEOUT):
                answer += chunk
                yield chunk
        except GroqTimeoutError:
            raise ExternalAPITimeoutException()
        except GroqAPIError:
            raise ExternalAPIException()

        ChatbotBaseService._store_history(key, history, ChatbotBaseService._build_messages(message, answer), ttl)
