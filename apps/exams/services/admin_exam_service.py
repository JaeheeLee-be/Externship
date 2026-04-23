from django.db.models import Count, Q, QuerySet

from apps.exams.exceptions.exam_exception import SubjectNotFound
from apps.exams.models import Exam
from apps.posts.models import Subject

ALLOWED_SORT_FIELDS = {
    "id",
    "title",
    "subject__title",
    "question_count",
    "submit_count",
    "created_at",
    "updated_at",
}


def get_exam_list(
    *, subject_id: int = None, search_keyword: str = None, sort: str = None, order: str = None
) -> QuerySet[Exam]:
    queryset = Exam.objects.all().order_by(
        "-created_at",
        "title",
    )

    if subject_id:
        queryset = queryset.filter(subject__id=subject_id)
    if search_keyword:
        queryset = queryset.filter(Q(title__icontains=search_keyword) | Q(subject__title__icontains=search_keyword))

    queryset = queryset.annotate(
        question_count=Count("examquestion", distinct=True),
        submit_count=Count("examdeployment__examsubmission", distinct=True),
    )

    if sort and sort in ALLOWED_SORT_FIELDS:
        ordering = f"-{sort}" if order == "desc" else sort
        queryset = queryset.order_by(ordering)

    return queryset


def create_exam(subject_id: int, title: str, thumbnail_image_url: str = None) -> Exam:
    if not Subject.objects.filter(id=subject_id).exists():
        raise SubjectNotFound()
    return Exam.objects.create(
        subject_id=subject_id,
        title=title,
        thumbnail_image_url=thumbnail_image_url,
    )
