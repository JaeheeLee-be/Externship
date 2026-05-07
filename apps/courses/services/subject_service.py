from typing import Any

from django.db import IntegrityError
from django.db.models import QuerySet

from apps.courses.models import Subject
from apps.courses.utils.exceptions import (
    CourseNotFoundError,
    SubjectDuplicateTitleError,
    SubjectNotFoundError,
)
from apps.posts.models import Course


def get_subject_list(course_id: int) -> QuerySet[Subject]:
    return Subject.objects.select_related("course").filter(course_id=course_id).order_by("id")


def create_subject(
    course_id: int,
    title: str,
    number_of_days: int,
    number_of_hours: int,
    thumbnail_img_url: str | None,
    status: bool = True,
) -> Subject:
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise CourseNotFoundError()
    try:
        return Subject.objects.create(
            course=course,
            title=title,
            number_of_days=number_of_days,
            number_of_hours=number_of_hours,
            thumbnail_img_url=thumbnail_img_url,
            status=status,
        )
    except IntegrityError:
        raise SubjectDuplicateTitleError()


def get_subject_detail(subject_id: int) -> Subject:
    try:
        return Subject.objects.select_related("course").get(id=subject_id)
    except Subject.DoesNotExist:
        raise SubjectNotFoundError("해당 과목을 찾을 수 없습니다.")


def update_subject(subject_id: int, **kwargs: Any) -> Subject:
    try:
        subject = Subject.objects.select_related("course").get(id=subject_id)
    except Subject.DoesNotExist:
        raise SubjectNotFoundError()
    for attr, value in kwargs.items():
        setattr(subject, attr, value)
    try:
        subject.save()
    except IntegrityError:
        raise SubjectDuplicateTitleError()
    return subject


def delete_subject(subject_id: int) -> None:
    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        raise SubjectNotFoundError()
    subject.delete()
