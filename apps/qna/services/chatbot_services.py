from dataclasses import asdict

from django.conf import settings

from apps.qna.chatbot import GROQ_MODEL, QNA_PROMPT, GroqFactory, call_groq_once
from apps.qna.models import Question, QuestionCategory
from apps.qna.redis import CacheRepository, CacheFactory, INITIAL_KEY






class InitialService:

    @staticmethod
    def save_initial_answer_in_redis(question: Question) -> None:
        category = InitialService._get_categories(question.category_id)
        save_data = CacheFactory.create_initial_cache(
            category=category,
            title=question.title,
            content=question.content,
            answer=InitialService._create_initial_answer(question, category),
        )

        key = INITIAL_KEY.format(question.id)
        CacheRepository.initial_save(key=key, value=asdict(save_data))

    @staticmethod
    def _create_initial_answer(question: Question, category: str) -> str:
        payload = GroqFactory.create_first_payload(
            prompt=QNA_PROMPT,
            category=category,
            title=question.title,
            message=question.content,
            stream=False,
        )
        return call_groq_once(asdict(payload), key=settings.GROQ_API_KEY)

    @staticmethod
    def _get_categories(category_id: int) -> str:  # 추후 카테고리 구현된거 보고 수정
        try:
            bottom = QuestionCategory.objects.select_related("parent__parent").get(pk=category_id)
            middle = bottom.parent
            top = middle.parent
            return f"카테고리: {top.name}-{middle.name}-{bottom.name}"
        except QuestionCategory.DoesNotExist:
            return ""