from dataclasses import asdict
from datetime import datetime
from time import sleep
from typing import Any, Iterator

from django.conf import settings

from apps.qna.chatbot import (
    GROQ_MODEL,
    QNA_PROMPT,
    GroqFactory,
    Message,
    call_groq,
    call_groq_once,
)
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
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
from apps.qna.redis import INITIAL_KEY, LOCK_KEY, CacheFactory, CacheRepository
from apps.qna.redis.dtos import InitialQNA
from apps.qna.redis.keys import QNA_KEY, SESSION_KEY


class InitialService:
    MODEL = GROQ_MODEL["gpt_120"]
    TTL = 60 * 60 * 24 * 7

    @staticmethod
    def get_initial_answer(question_id: int) -> InitialQNA:

        key = INITIAL_KEY.format(question_id)
        cached = CacheRepository.get_initial(key)
        if cached:
            return cached

        lock_key = LOCK_KEY.format(key)
        if not CacheRepository.acquire_lock(lock_key):
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
        CacheRepository.save_initial(key=key, value=asdict(save_data), ttl=InitialService.TTL)

        return save_data

    @staticmethod
    def _create_initial_answer(question: Question, categories: str) -> str:
        payload = GroqFactory.create_initial_payload(
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


class QNAChatbotService:
    MODEL = GROQ_MODEL["gpt_120"]
    TTL = 60 * 30

    @staticmethod
    def response_history(user_id: int, question_id: int) -> list[Message]:
        """
        qna 채팅 히스토리 조회용 함수입니다.
        유저가 히스토리를 조회함으로써 세션이 처음 활성화됩니다.
        히스토리가 없는 경우 빈 문자열을 반환합니다.
        채팅 히스토리에는 초기응답이 포함되지 않지만, 올바른 question_id를 체크하기 위해
        ensure_initial_exist를 사용합니다.
        """
        QNAChatbotService.ensure_initial_exist(question_id)
        QNAChatbotService._make_session(user_id, question_id)
        history = CacheRepository.get_history(QNA_KEY.format(user_id, question_id))
        return history or []

    @staticmethod
    def stream_chat(user_id: int, question_id: int, message: str) -> Iterator[str]:
        """
        qna 채팅 대화용 함수입니다.
        대화 히스토리를 챗봇에게 넘겨주기 위해 캐시 조회를 하며,
        유저의 질문과 챗봇의 응답 한 쌍을 하나의 대화로 취급합니다.
        만약 대화의 길이가 5쌍 이상일 경우, 사용자의 다음 채팅에 대해 429를 반환합니다.
        ttl은 30분이며, 대화가 갱신될때마다 같이 갱신됩니다.
        """
        history = CacheRepository.get_history(QNA_KEY.format(user_id, question_id))
        if history is not None and len(history) >= 10:
            raise ConversationOverException()
        initial = CacheRepository.get_initial(INITIAL_KEY.format(question_id))
        if initial is None:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")
        payload = GroqFactory.create_payload(
            prompt=QNA_PROMPT,
            message=message,
            history=QNAChatbotService._build_history_for_payload(initial, history),
            model=QNAChatbotService.MODEL,
        )

        try:
            answer = ""

            for chunk in call_groq(asdict(payload), settings.GROQ_API_KEY, timeout=(5, 60)):
                answer += chunk
                yield chunk
        except GroqTimeoutError:
            raise ExternalAPITimeoutException()
        except GroqAPIError:
            raise ExternalAPIException()

        QNAChatbotService._store_history(
            user_id, question_id, QNAChatbotService.TTL, QNAChatbotService._build_messages(message, answer)
        )

    @staticmethod
    def ensure_active_session(user_id: int, question_id: int) -> None:
        if not QNAChatbotService._check_session(user_id, question_id):
            raise InactiveSessionException()

    @staticmethod
    def ensure_initial_exist(question_id: int) -> None:
        initial = CacheRepository.get_initial(INITIAL_KEY.format(question_id))
        if initial is None:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")

    @staticmethod
    def ensure_conversation_not_over(user_id: int, question_id: int) -> None:
        history = CacheRepository.get_history(QNA_KEY.format(user_id, question_id))
        if history is not None and len(history) >= 10:
            raise ConversationOverException()

    @staticmethod
    def _make_session(user_id: int, question_id: int) -> None:
        CacheRepository.set_session(key=SESSION_KEY.format(user_id), value=question_id, ttl=QNAChatbotService.TTL)

    @staticmethod
    def _build_history_for_payload(
        initial: InitialQNA,
        history: list[Message] | None = None,
    ) -> list[Message]:
        initial_history = [
            Message(
                role="user",
                content=f"""
                    <category>{initial.category}</category>
                    <client_question>
                        <title>{initial.title}</title>
                        <message>{initial.content}</message>
                    </client_question>
                """,
            ),
            Message(role="assistant", content=initial.answer),
        ]

        return initial_history + (history or [])

    @staticmethod
    def _store_history(user_id: int, question_id: int, ttl: int, messages: list[Message]) -> None:
        key = QNA_KEY.format(user_id, question_id)
        history = CacheRepository.get_history(key)

        if history is None:
            CacheRepository.save_history(
                key=key,
                history=[asdict(m) for m in messages],
                ttl=ttl,
            )
            QNAChatbotService._make_session(user_id, question_id)
        elif len(history) < 10:
            CacheRepository.save_history(
                key=key,
                history=[asdict(m) for m in (history + messages)],
                ttl=ttl,
            )
            QNAChatbotService._make_session(user_id, question_id)

    @staticmethod
    def _build_messages(message: str, answer: str) -> list[Message]:
        return [
            Message(role="user", content=message),
            Message(role="assistant", content=answer, timestamp=datetime.now().isoformat()),
        ]

    @staticmethod
    def _check_session(user_id: int, question_id: int) -> bool:
        return CacheRepository.get_session(SESSION_KEY.format(user_id)) == question_id
