from dataclasses import asdict

from django.conf import settings

from apps.qna.chatbot import GROQ_MODEL, QNA_PROMPT, GroqFactory, call_groq_once
from apps.qna.models import Question, QuestionCategory


def get_categories(category_id: int) -> str:
    try:
        bottom = QuestionCategory.objects.select_related("parent__parent").get(pk=category_id)
        middle = bottom.parent
        top = middle.parent
        return f"카테고리: {top.name}-{middle.name}-{bottom.name}"
    except QuestionCategory.DoesNotExist:
        return ""


def create_first_answer(question: Question) -> str:
    payload = GroqFactory.create_first_payload(
        prompt=QNA_PROMPT,
        category=get_categories(question.category_id),
        title=question.title,
        message=question.content,
        stream=False,
    )
    return call_groq_once(asdict(payload), key=settings.GROQ_API_KEY)
