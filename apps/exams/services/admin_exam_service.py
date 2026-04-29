from typing import Optional

from django.db.models import Count, Q, QuerySet

from apps.exams.exceptions.exam_exception import (
    ExamDeleteConflict,
    ExamTitleConflict,
    SubjectNotFound,
)
from apps.exams.models import Exam, ExamDeployment
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
    *,
    subject_id: Optional[int] = None,
    search_keyword: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> QuerySet[Exam]:
    queryset = (
        Exam.objects.all()
        .select_related("subject")
        .order_by(
            "-created_at",
            "title",
        )
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


def create_exam(subject_id: int, title: str, thumbnail_image_url: str = "default_img_url") -> Exam:
    if not Subject.objects.filter(id=subject_id).exists():
        raise SubjectNotFound()
    if Exam.objects.filter(title=title).exists():
        raise ExamTitleConflict()
    return Exam.objects.create(subject_id=subject_id, title=title, thumbnail_image_url=thumbnail_image_url)


def get_exam(exam_id: int) -> Exam:
    try:
        return Exam.objects.select_related("subject").prefetch_related("examquestion_set").get(pk=exam_id)
    except Exam.DoesNotExist:
        raise ValueError("해당 쪽지시험 정보를 찾을 수 없습니다.")


def put_exam(exam_id: int, title: str, subject_id: int, thumbnail_image_url: str) -> Exam:
    try:
        exam = Exam.objects.get(pk=exam_id)
    except Exam.DoesNotExist:
        raise ValueError("해당 쪽지시험 정보를 찾을 수 없습니다.")
    if not Subject.objects.filter(id=subject_id).exists():
        raise SubjectNotFound()
    if Exam.objects.filter(title=title).exclude(pk=exam_id).exists():
        raise ExamTitleConflict()

    exam.title = title
    exam.subject_id = subject_id
    exam.thumbnail_image_url = thumbnail_image_url
    exam.save()
    return exam


def delete_exam(exam_id: int) -> None:
    try:
        exam = Exam.objects.get(pk=exam_id)
    except Exam.DoesNotExist:
        raise ValueError("삭제하려는 쪽지시험 정보를 찾을 수 없습니다.")

    if ExamDeployment.objects.filter(exam=exam).exists():
        raise ExamDeleteConflict()

    exam.delete()
