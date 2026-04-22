from django.db.models import Count, Q, QuerySet

from apps.exams.exceptions.exam_exception import SubjectNotFound
from apps.exams.models import Exam


def get_exam_list(*, subject: int = None, search: str = None) -> QuerySet[Exam]:
    queryset = Exam.objects.all().order_by(
        "-created_at",
        "title",
    )

    if subject:
        queryset = queryset.filter(subject__id=subject)
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(subject__title__icontains=search))

    queryset = queryset.annotate(
        question_count=Count("examquestion", distinct=True),
        submit_count=Count("examdeployment__examsubmission", distinct=True),
    )

    return queryset


def create_exam(*, subject: int, title: str, thumbnail_image_url: str = None) -> Exam:
    if not Subject.objects.filter(id=subject).exists():
        raise SubjectNotFound()
    return Exam.objects.create(
        subject_id=subject,
        title=title,
        thumbnail_image_url=thumbnail_image_url,
    )
