from django.db import transaction

from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import User


class QuestionService:

    @staticmethod
    @transaction.atomic
    def create_question(
        *,
        author: User,
        title: str,
        content: str,
        category: QuestionCategory,
        img_urls: list[str],
    ) -> Question:
        question = Question.objects.create(
            author=author,
            title=title,
            content=content,
            category=category,
        )

        if img_urls:
            QuestionImage.objects.bulk_create([QuestionImage(question=question, img_url=url) for url in img_urls])

        return question
