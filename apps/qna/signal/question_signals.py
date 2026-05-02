from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.qna.models import Question
from apps.qna.services.chatbot_services import InitialService as Init


@receiver(post_save, sender=Question)
def handle_question_created(sender, created, **kwargs) -> None:
    if not created:
        return
    Init.save_initial_answer_in_redis(kwargs["instance"])
