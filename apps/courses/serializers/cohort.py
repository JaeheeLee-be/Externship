from typing import Any

from rest_framework import serializers

from apps.courses.models import Cohort
from apps.posts.models import Course
from apps.users.models import User


class CohortCourseSerializer(serializers.ModelSerializer[Course]):

    class Meta:
        model = Course
        fields = ("id", "name", "tag")


class CohortCreateSerializer(serializers.ModelSerializer[Cohort]):
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
        extra_kwargs = {"status": {"required": False}}

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": ["종료일은 시작일 이후여야 합니다."]})
        return attrs


class CohortListSerializer(serializers.ModelSerializer[Cohort]):

    class Meta:
        model = Cohort
        fields = ("id", "course_id", "number", "status")


class CohortDetailSerializer(serializers.ModelSerializer[Cohort]):
    course = CohortCourseSerializer(read_only=True)

    class Meta:
        model = Cohort
        fields = (
            "id",
            "course",
            "number",
            "max_student",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        )


class CohortUpdateSerializer(serializers.ModelSerializer[Cohort]):

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
        read_only_fields = ("id", "course_id", "updated_at")
        extra_kwargs = {
            "number": {"required": False},
            "max_student": {"required": False},
            "start_date": {"required": False},
            "end_date": {"required": False},
            "status": {"required": False},
        }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance = self.instance if isinstance(self.instance, Cohort) else None
        start_date = attrs.get("start_date", instance.start_date if instance else None)
        end_date = attrs.get("end_date", instance.end_date if instance else None)
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": ["종료일은 시작일 이후여야 합니다."]})
        return attrs


class CohortAvgScoreSerializer(serializers.Serializer[None]):
    name = serializers.CharField()
    score = serializers.IntegerField()


class CohortStudentSerializer(serializers.ModelSerializer[User]):
    value = serializers.CharField(source="nickname")
    label = serializers.CharField(source="name")  # type: ignore[assignment]

    class Meta:
        model = User
        fields = ("value", "label")
