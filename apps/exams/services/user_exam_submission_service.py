from django.db.models import QuerySet

from apps.exams.exceptions.exam_submission_exception import UserSubmissionNotFound
from apps.exams.models import ExamSubmission


def get_submission_detail(submitter: int, submission_id: int) -> ExamSubmission:
    try:
        return ExamSubmission.objects.select_related("deployment__exam__subject").get(
            submitter=submitter, id=submission_id
        )
    except ExamSubmission.DoesNotExist:
        raise UserSubmissionNotFound()
