from typing import Iterator

from apps.qna.chatbot import CS_PROMPT, GROQ_MODEL, GroqPayloadFactory
from apps.qna.dtos import Message
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import CS_KEY
from apps.qna.services.chatbot_base import ChatbotBaseService


class CSChatbotService(ChatbotBaseService):
    MODEL = GROQ_MODEL["gpt_120"]
    CS_TTL = 60 * 30

    @staticmethod
    def response_cs_history(user_id: int) -> list[Message]:
        history = CacheRepository.get_history(CS_KEY.format(user_id=user_id))
        return history or []

    @staticmethod
    def response_cs_chat(user_id: int, message: str) -> Iterator[str]:
        history = CacheRepository.get_history(CS_KEY.format(user_id=user_id))
        payload = GroqPayloadFactory.create_payload(
            prompt=CS_PROMPT,
            message=message,
            history=history,
            model=CSChatbotService.MODEL,
        )
        key = CS_KEY.format(user_id=user_id)
        return CSChatbotService._stream_and_save_chat(key, history, message, payload, ttl=CSChatbotService.CS_TTL)
