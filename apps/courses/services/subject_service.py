from django.db import IntegrityError
from django.db.models import QuerySet

from apps.courses.exceptions import SubjectDuplicateTitleError, SubjectNotFoundError
from apps.courses.models import Course, Subject


def create_subject(
    course: Course,
    title: str,
    number_of_days: int,
    number_of_hours: int,
    thumbnail_img_url: str | None,
) -> Subject:
    try:
        return Subject.objects.create(
            course=course,
            title=title,
            number_of_days=number_of_days,
            number_of_hours=number_of_hours,
            thumbnail_img_url=thumbnail_img_url,
        )
    except IntegrityError:
        raise SubjectDuplicateTitleError("동일한 이름의 과목이 이미 존재합니다.")


def get_subject_list(course_id: int, page: int, page_size: int) -> tuple[int, QuerySet[Subject]]:
    qs = Subject.objects.select_related("course").filter(course_id=course_id).order_by("id")
    total_count = qs.count()
    offset = (page - 1) * page_size
    return total_count, qs[offset : offset + page_size]


def get_subject_detail(subject_id: int) -> Subject:
    try:
        return Subject.objects.select_related("course").get(id=subject_id)
    except Subject.DoesNotExist:
        raise SubjectNotFoundError("해당 과목을 찾을 수 없습니다.")
