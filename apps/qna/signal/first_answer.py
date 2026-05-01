from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.qna.models import Question
from apps.qna.services.chatbot_services import create_first_answer


@receiver(post_save, sender=Question)
def handle_question_created(sender, **kwargs):
    return create_first_answer(kwargs["instance"])
