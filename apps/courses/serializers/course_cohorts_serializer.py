from typing import Any

from rest_framework import serializers

from apps.courses.models import Cohort
from apps.posts.models import Course
from apps.users.models import User


class CohortDateRangeMixin:
    # POST api/v1/admin/cohorts, PATCH api/v1/admin/cohorts/{cohort_id}
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        raw_instance = getattr(self, "instance", None)
        instance = raw_instance if isinstance(raw_instance, Cohort) else None

        start_date = attrs.get("start_date", instance.start_date if instance else None)
        end_date = attrs.get("end_date", instance.end_date if instance else None)

        if start_date is not None and end_date is not None and end_date <= start_date:
            raise serializers.ValidationError({"end_date": ["종료일은 시작일 이후여야 합니다."]})

        return attrs


# GET api/v1/admin/cohorts/{cohort_id} response nested cohort
class CohortCourseSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name", "tag")


# POST api/v1/admin/cohorts request
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


# POST api/v1/admin/cohorts 201 response
class CohortCreateResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = serializers.CharField(default="기수가 등록되었습니다.")
    id = serializers.IntegerField()


# GET api/v1/courses/{course_id}/cohorts response
class CohortListSerializer(serializers.ModelSerializer[Cohort]):
    cohort_id = serializers.IntegerField(source="course_id", read_only=True)

    class Meta:
        model = Cohort
        fields = ("id", "cohort_id", "number", "status")
        read_only_fields = fields


# GET api/v1/admin/cohorts/{cohort_id} response
class CohortDetailSerializer(serializers.ModelSerializer[Cohort]):
    cohort = CohortCourseSerializer(source="course", read_only=True)

    class Meta:
        model = Cohort
        fields = (
            "id",
            "cohort",
            "number",
            "max_student",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# PATCH api/v1/admin/cohorts/{cohort_id} request
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


# PATCH api/v1/admin/cohorts/{cohort_id} 200 response
class CohortUpdateResponseSerializer(serializers.ModelSerializer[Cohort]):
    cohort_id = serializers.IntegerField(source="course_id", read_only=True)

    class Meta:
        model = Cohort
        fields = (
            "id",
            "cohort_id",
            "number",
            "max_student",
            "start_date",
            "end_date",
            "status",
            "updated_at",
        )
        read_only_fields = fields


# GET api/v1/admin/courses/{course_id}/cohorts/avg-scores response
class CohortAvgScoreSerializer(serializers.Serializer[dict[str, Any]]):
    name = serializers.CharField()
    score = serializers.IntegerField()


# GET api/v1/admin/cohorts/{cohort_id}/students response
class CohortStudentSerializer(serializers.ModelSerializer[User]):
    value = serializers.CharField(source="nickname")
    label = serializers.CharField(source="name")  # type: ignore[assignment]

    class Meta:
        model = User
        fields = ("value", "label")
