from dataclasses import asdict
from typing import reveal_type

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
    def save_initial_answer_for_created(question_id: int) -> InitialQNA:
        if CacheRepository.get(INITIAL_KEY.format(question_id)):
            raise ConflictException("이미 AI가 답변을 생성했습니다.")
        question = Question.objects.filter(pk=question_id).select_related("category__parent__parent").first()
        if not question:
            raise NotFoundException("질문 데이터를 찾을 수 없습니다.")
        return InitialService.save_initial_answer(question)

    @staticmethod
    def save_initial_answer(question: Question) -> InitialQNA:
        category = InitialService._get_categories(question.category)
        save_data = CacheFactory.create_initial_cache(
            category=category,
            title=question.title,
            content=question.content,
            answer=InitialService._create_initial_answer(question, category),
            question_id=question.id,
            using_model=InitialService.MODEL,
        )

        key = INITIAL_KEY.format(question.id)
        CacheRepository.initial_save(key=key, value=asdict(save_data), ttl=InitialService.TTL)

        return save_data

    @staticmethod
    def get_initial_answer(question_id: int) -> InitialQNA:
        key = INITIAL_KEY.format(question_id)
        cached = CacheRepository.get(key)
        if cached:
            return cached

        question = Question.objects.filter(pk=question_id).select_related("category__parent__parent").first()
        if not question:
            raise NotFoundException("질문 데이터를 찾을 수 없습니다.")

        lock_key = LOCK_KEY.format(key)
        if not CacheRepository.acquire_lock(lock_key):
            raise ConflictException("이미 AI가 답변을 생성했습니다.")

        try:
            return InitialService.save_initial_answer(question)
        finally:
            CacheRepository.delete(lock_key)

    @staticmethod
    def _create_initial_answer(question: Question, category: str) -> str:
        payload = GroqFactory.create_initial_payload(
            prompt=QNA_PROMPT,
            category=category,
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
            return ""

        top = middle.parent
        if top is None:
            return ""

        return f"{top.name} > {middle.name} > {category.name}"
