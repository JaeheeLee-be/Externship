from dataclasses import asdict
from datetime import datetime
from time import sleep
from typing import Iterator

from django.conf import settings

from apps.qna.chatbot import (
    GROQ_MODEL,
    QNA_PROMPT,
    GroqPayloadFactory,
    call_groq,
    call_groq_once,
)
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.dtos import GroqPayload, InitialQNA, Message
from apps.qna.exceptions import (
    ConflictException,
    ConversationOverException,
    ExternalAPIException,
    ExternalAPITimeoutException,
    GetInitialTimeoutException,
    InactiveSessionException,
    NotFoundException,
)
from apps.qna.models import Question, QuestionCategory
from apps.qna.redis import CacheFactory, CacheRepository
from apps.qna.redis.keys import INITIAL_KEY, LOCK_KEY, QNA_KEY, SESSION_KEY


class InitialService:
    MODEL = GROQ_MODEL["gpt_120"]
    INITIAL_TTL = 60 * 60 * 24 * 7
    LOCK_TTL = 60

    @staticmethod
    def get_initial_answer(question_id: int) -> InitialQNA:

        key = INITIAL_KEY.format(question_id)
        cached = CacheRepository.get_initial(key)
        if cached:
            return cached

        lock_key = LOCK_KEY.format(key)
        if not CacheRepository.acquire_lock(lock_key, InitialService.LOCK_TTL):
            timeout = 20
            interval = 2
            elapsed = 0
            while elapsed < timeout:
                sleep(interval)
                elapsed += interval
                cached = CacheRepository.get_initial(key)
                if cached:
                    return cached
            raise GetInitialTimeoutException()

        try:
            return InitialService.save_initial_answer(question_id)
        finally:
            CacheRepository.delete(lock_key)

    @staticmethod
    def save_initial_answer(question_id: int) -> InitialQNA:
        """
        초기응답 생성용 서비스 함수입니다.
        동시요청 가능성이 없어 락을 구현하지 않았습니다.
        초기응답은 모든 클라이언트에게 동일하게 제공되므로 캐시 키에 user_id를 포함하지 않습니다.
        """
        if CacheRepository.get_initial(INITIAL_KEY.format(question_id)):
            raise ConflictException("이미 AI가 답변을 생성했습니다.")

        question = Question.objects.filter(pk=question_id).select_related("category__parent__parent").first()
        if not question:
            raise NotFoundException("질문 데이터를 찾을 수 없습니다.")

        categories = InitialService._get_categories(question.category)
        save_data = CacheFactory.create_initial_cache(
            category=categories,
            title=question.title,
            content=question.content,
            answer=InitialService._create_initial_answer(question, categories),
            question_id=question.id,
            using_model=InitialService.MODEL,
        )

        key = INITIAL_KEY.format(question.id)
        CacheRepository.save_initial(key=key, value=asdict(save_data), ttl=InitialService.INITIAL_TTL)

        return save_data

    @staticmethod
    def _create_initial_answer(question: Question, categories: str) -> str:
        payload = GroqPayloadFactory.create_initial_payload(
            prompt=QNA_PROMPT,
            category=categories,
            title=question.title,
            message=question.content,
            stream=False,
            model=InitialService.MODEL,
        )

        try:
            return call_groq_once(asdict(payload), key=settings.GROQ_API_KEY, timeout=(5, 60))
        except GroqTimeoutError:
            raise ExternalAPITimeoutException()
        except GroqAPIError:
            raise ExternalAPIException()

    @staticmethod
    def _get_categories(category: QuestionCategory) -> str:
        middle = category.parent
        if middle is None:
            return category.name

        top = middle.parent
        if top is None:
            return f"{middle.name} > {category.name}"

        return f"{top.name} > {middle.name} > {category.name}"


class ChatbotService:
    MODEL = GROQ_MODEL["gpt_120"]
    QNA_TTL = 60 * 30

    @staticmethod
    def response_qna_history(user_id: int, question_id: int) -> list[Message]:
        """
        qna 채팅 히스토리 조회용 함수입니다.
        유저가 히스토리를 조회함으로써 세션이 처음 활성화됩니다.
        히스토리가 없는 경우 빈 문자열을 반환합니다.
        """
        initial = CacheRepository.get_initial(INITIAL_KEY.format(question_id))
        if initial is None:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")
        return ChatbotService._response_history(user_id, question_id)

    @staticmethod
    def response_qna_chat(user_id: int, question_id: int, message: str) -> Iterator[str]:
        """
        qna 채팅 대화용 함수입니다.
        세션 활성화는 히스토리 조회에서 이뤄지고, 이곳에서는 해당 세션을 검증합니다.
        유저의 질문과 챗봇의 응답 한 쌍을 하나의 대화로 취급되며,
        만약 캐시에 저장된 대화의 길이가 5쌍 이상일 경우, 사용자의 다음 채팅에 대해 429를 반환합니다.
        대화 히스토리와 세션의 ttl은 30분이며, 대화가 갱신될때마다 같이 갱신됩니다.
        """
        history = CacheRepository.get_history(QNA_KEY.format(user_id, question_id))
        initial = CacheRepository.get_initial(INITIAL_KEY.format(question_id))
        assert initial is not None
        payload = GroqPayloadFactory.create_payload(
            prompt=QNA_PROMPT,
            message=message,
            history=GroqPayloadFactory.build_history_for_qna_payload(initial, history),
            model=ChatbotService.MODEL,
        )
        key = QNA_KEY.format(user_id, question_id)

        ChatbotService._make_session(user_id, question_id)
        return ChatbotService._stream_and_save_chat(key, history, message, payload)

    @staticmethod
    def validate_qna_chat(user_id: int, question_id: int) -> None:
        """StreamingHttpResponse를 사용하면 에러 상태코드가 제대로 나가지 않아서 분리함"""
        if not CacheRepository.get_session(SESSION_KEY.format(user_id)) == question_id:
            raise InactiveSessionException()
        history = CacheRepository.get_history(QNA_KEY.format(user_id, question_id))
        if history is not None and len(history) >= 10:
            raise ConversationOverException()
        if CacheRepository.get_initial(INITIAL_KEY.format(question_id)) is None:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")

    @staticmethod
    def _response_history(user_id: int, question_id: int) -> list[Message]:
        ChatbotService._make_session(user_id, question_id)
        history = CacheRepository.get_history(QNA_KEY.format(user_id, question_id))
        return history or []

    @staticmethod
    def _stream_and_save_chat(
        key: str, history: list[Message] | None, message: str, payload: GroqPayload
    ) -> Iterator[str]:
        try:
            answer = ""
            for chunk in call_groq(asdict(payload), settings.GROQ_API_KEY, timeout=(5, 60)):
                answer += chunk
                yield chunk
        except GroqTimeoutError:
            raise ExternalAPITimeoutException()
        except GroqAPIError:
            raise ExternalAPIException()

        ChatbotService._store_history(
            key, history, ChatbotService._build_messages(message, answer), ChatbotService.QNA_TTL
        )

    @staticmethod
    def _make_session(user_id: int, question_id: int) -> None:
        CacheRepository.set_session(key=SESSION_KEY.format(user_id), value=question_id, ttl=ChatbotService.QNA_TTL)

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
            Message(role="assistant", content=answer, timestamp=datetime.now().isoformat()),
        ]
