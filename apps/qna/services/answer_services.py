from typing import Any

from django.db import transaction
from rest_framework.exceptions import NotFound

from apps.qna.models.answer_models import Answer, AnswerImage
from apps.qna.models.question_models import Question
from apps.users.models import User


class AnswerService:
    def get_question(self, question_id: int) -> Question:
        try:
            return Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            raise NotFound("해당 질문을 찾을 수 없습니다.")

    def answer_create(self, user: User, question_id: int, **validated_data: Any) -> Answer:
        with transaction.atomic():
            answer = Answer.objects.create(
                author_id=user.id,
                question_id=question_id,
                content=validated_data["content"],
            )
            AnswerImage.objects.bulk_create(
                [AnswerImage(img_url=img, answer=answer) for img in validated_data.get("img_urls", [])]
            )
        return answer
