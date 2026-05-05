from dataclasses import asdict

from django.conf import settings

from apps.qna.chatbot import GROQ_MODEL, QNA_PROMPT, GroqFactory, call_groq_once
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.exceptions import (
    ConflictException,
    ExternalAPIException,
    ExternalAPITimeoutException,
    NotFoundException,
)
from apps.qna.models import Question, QuestionCategory
from apps.qna.redis import INITIAL_KEY, LOCK_KEY, CacheFactory, CacheRepository
from apps.qna.redis.dtos import InitialQNA


class InitialService:
    MODEL = GROQ_MODEL["gpt_120"]
    TTL = 60 * 60 * 24 * 7

    @staticmethod
    def get_initial_answer(question_id: int) -> InitialQNA:
        """
        초기응답 조회용 서비스 함수입니다.
        조회했을 때 AI 초기응답이 없을 시 초기응답을 재요청하게 됩니다.
        중복 생성을 방지하기 위해 락으로 동시성 제어를 구현했습니다.
        """
        key = INITIAL_KEY.format(question_id)
        cached = CacheRepository.get(key)
        if cached:
            return cached

        lock_key = LOCK_KEY.format(key)
        if not CacheRepository.acquire_lock(lock_key):
            raise ConflictException("이미 AI가 답변을 생성했습니다.")

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
        if CacheRepository.get(INITIAL_KEY.format(question_id)):
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
        CacheRepository.initial_save(key=key, value=asdict(save_data), ttl=InitialService.TTL)

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
            return call_groq_once(asdict(payload), key=settings.GROQ_API_KEY)
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
