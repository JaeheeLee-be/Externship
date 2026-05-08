from typing import Any

from rest_framework import serializers

from apps.courses.models import Cohort
from apps.posts.models import Course
from apps.users.models import User


class CohortDateRangeMixin:
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        raw_instance = getattr(self, "instance", None)
        instance = raw_instance if isinstance(raw_instance, Cohort) else None

        start_date = attrs.get("start_date", instance.start_date if instance else None)
        end_date = attrs.get("end_date", instance.end_date if instance else None)

        if start_date is not None and end_date is not None and end_date <= start_date:
            raise serializers.ValidationError({"end_date": ["종료일은 시작일 이후여야 합니다."]})

        return attrs


class CohortCourseSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name", "tag", "description")


class CohortCreateSerializer(CohortDateRangeMixin, serializers.ModelSerializer[Cohort]):
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
    )

    class Meta:
        model = Cohort
        fields = (
            "course_id",
            "number",
            "max_student",
            "start_date",
            "end_date",
            "status",
        )
        extra_kwargs = {
            "status": {"required": False},
        }


class CohortCreateResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = serializers.CharField(default="기수가 등록되었습니다.")
    id = serializers.IntegerField()


class CohortListSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "course_id", "number", "status")
        read_only_fields = fields


class CohortAdminListSerializer(serializers.ModelSerializer[Cohort]):
    course = CohortCourseSerializer(read_only=True)
    course_cohort = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Cohort
        fields = (
            "id",
            "course",
            "course_cohort",
            "student_count",
            "status",
            "start_date",
            "end_date",
        )
        read_only_fields = fields

    def get_course_cohort(self, obj: Cohort) -> str:
        return f"{obj.course.name} {obj.number}기"

    def get_student_count(self, obj: Cohort) -> int:
        return get_cohort_student_count(obj)


class CohortDetailSerializer(serializers.ModelSerializer[Cohort]):
    course = CohortCourseSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Cohort
        fields = (
            "id",
            "created_at",
            "updated_at",
            "course",
            "number",
            "max_student",
            "student_count",
            "start_date",
            "end_date",
            "status",
        )
        read_only_fields = fields

    def get_student_count(self, obj: Cohort) -> int:
        return get_cohort_student_count(obj)


class CohortUpdateSerializer(CohortDateRangeMixin, serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = (
            "number",
            "max_student",
            "start_date",
            "end_date",
            "status",
        )
        extra_kwargs = {
            "number": {"required": False},
            "max_student": {"required": False},
            "start_date": {"required": False},
            "end_date": {"required": False},
            "status": {"required": False},
        }


class CohortUpdateResponseSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = (
            "id",
            "course_id",
            "number",
            "max_student",
            "start_date",
            "end_date",
            "status",
            "updated_at",
        )
        read_only_fields = fields


class CohortAvgScoreSerializer(serializers.Serializer[dict[str, Any]]):
    name = serializers.CharField()
    score = serializers.IntegerField()


class CohortStudentSerializer(serializers.ModelSerializer[User]):
    value = serializers.CharField(source="nickname")
    label = serializers.CharField(source="name")  # type: ignore[assignment]

    class Meta:
        model = User
        fields = ("value", "label")


def get_cohort_student_count(obj: Cohort) -> int:
    student_count = getattr(obj, "student_count", None)
    if student_count is not None:
        return int(student_count)

    cohort_students = getattr(obj, "cohortstudents_set", None)
    if cohort_students is None:
        return 0
    return int(cohort_students.count())
