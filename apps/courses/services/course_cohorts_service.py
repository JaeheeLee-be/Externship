from typing import Any

from django.db import IntegrityError
from django.db.models import Avg, QuerySet
from rest_framework.exceptions import ValidationError

from apps.courses.models import Cohort
from apps.courses.utils.exceptions import CohortNotFoundError, CourseNotFoundError
from apps.posts.models import Course
from apps.users.models import User


def get_cohorts_by_course(course_id: int) -> QuerySet[Cohort]:
    return Cohort.objects.filter(course_id=course_id).order_by("id")


def create_cohort(validated_data: dict[str, Any]) -> Cohort:
    try:
        return Cohort.objects.create(**validated_data)
    except IntegrityError as exc:
        raise ValidationError({"number": ["이미 등록된 기수입니다."]}) from exc


def get_cohort(cohort_id: int, *, not_found_message: str = "기수를 찾을 수 없습니다.") -> Cohort:
    try:
        return Cohort.objects.select_related("course").get(id=cohort_id)
    except Cohort.DoesNotExist as exc:
        raise CohortNotFoundError(not_found_message) from exc


def update_cohort(cohort: Cohort, validated_data: dict[str, Any]) -> Cohort:
    for field, value in validated_data.items():
        setattr(cohort, field, value)

    if validated_data:
        try:
            cohort.save(update_fields=[*validated_data.keys(), "updated_at"])
        except IntegrityError as exc:
            raise ValidationError({"number": ["이미 등록된 기수입니다."]}) from exc

    return cohort


def get_cohort_avg_scores(course_id: int) -> list[dict[str, int | str]]:
    if not Course.objects.filter(id=course_id).exists():
        raise CourseNotFoundError("과정을 찾을 수 없습니다.")

    cohorts = (
        Cohort.objects.filter(course_id=course_id)
        .annotate(avg_score=Avg("examdeployment__examsubmission__score"))
        .order_by("number")
    )

    results: list[dict[str, int | str]] = []
    for cohort in cohorts:
        avg_score = getattr(cohort, "avg_score", None)
        score = int(round(avg_score)) if avg_score is not None else 0
        results.append({"name": f"{cohort.number}기", "score": score})

    return results


def get_cohort_students(cohort_id: int) -> QuerySet[User]:
    get_cohort(cohort_id)

    return User.objects.filter(cohort_students__cohort_id=cohort_id).order_by("id")
