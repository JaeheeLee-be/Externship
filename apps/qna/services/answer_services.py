from typing import Any

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.qna.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
)
from apps.qna.models.answer_models import Answer, AnswerImage
from apps.qna.models.question_models import Question
from apps.users.models import User


class AnswerService:
    """
    답변 생성 API 구현을 위한 서비스 class
    """

    def get_question(self, question_id: int) -> Question:
        """어떤 질문에 답변을 달지 가져오는 함수"""
        try:
            return Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")

    def answer_create(self, user: User, question_id: int, **validated_data: Any) -> Answer:
        """답변 생성 로직"""
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


class AnswerAcceptService:
    """
    답변 채택 로직
    """

    def answer_accept(self, user: User, answer_id: int) -> Answer:
        """질문을 작성한 작성자만 채택이 가능 하며 이미 채택된 답글이 있으면 에러 발생"""
        with transaction.atomic():
            try:
                answer = Answer.objects.select_for_update().select_related("question").get(pk=answer_id)
            except Answer.DoesNotExist:
                raise NotFoundException("해당 질문 또는 답변을 찾을 수 없습니다.")
            if answer.question.author_id != user.id:
                raise PermissionDeniedException("본인이 작성한 질문의 답변만 채택할 수 있습니다.")
            if Answer.objects.filter(question_id=answer.question_id, is_adopted=True).exists():
                raise ConflictException()
            answer.is_adopted = True
            answer.save()
            return answer


class AnswerDetailService:
    """
    답변 수정 API 구현을 위한 class
    """

    def get_answer(self, answer_id: int) -> Answer:
        """어떤 답변을 수정할지 가져오는 함수"""
        try:
            return Answer.objects.get(pk=answer_id)
        except Answer.DoesNotExist:
            raise NotFoundException("해당 답변을 찾을 수 없습니다.")

    def update(self, user: User, answer: Answer, **validated_data: Any) -> Answer:
        """답변 수정을 위한 로직"""
        if answer.author_id != user.id:
            raise PermissionDeniedException("본인이 작성한 답변만 수정할 수 있습니다.")
        with transaction.atomic():
            answer.content = validated_data["content"]
            answer.save()

            answer.answerimage_set.all().delete()
            AnswerImage.objects.bulk_create(
                [AnswerImage(img_url=img, answer=answer) for img in validated_data.get("img_urls", [])]
            )
        return answer
