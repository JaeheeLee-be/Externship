from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.exams.models.exam_model import Exam
from apps.posts.models.cohort import Cohort
from apps.posts.models.course import Course
from apps.posts.models.subject import Subject


class SubjectSummarySerializer(serializers.ModelSerializer[Subject]):
    class Meta:
        model = Subject
        fields = ["id", "title"]


class ExamSummarySerializer(serializers.ModelSerializer[Exam]):
    class Meta:
        model = Exam
        fields = ["id", "title", "thumbnail_image_url"]


class CourseSummarySerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ["id", "name", "tag"]


class CohortSummarySerializer(serializers.ModelSerializer[Cohort]):
    course = CourseSummarySerializer()
    display = serializers.SerializerMethodField()

    def get_display(self, obj: Cohort) -> str:
        return f"{obj.course.name} {obj.number}기"

    class Meta:
        model = Cohort
        fields = ["id", "number", "display", "course"]


class AdminExamDeploymentCreateSerializer(serializers.Serializer[Any]):
    exam_id = serializers.IntegerField()
    cohort_id = serializers.IntegerField()
    duration_time = serializers.IntegerField(
        min_value=1,
        max_value=99,
        default=60,
    )
    open_at = serializers.DateTimeField()
    close_at = serializers.DateTimeField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        now = timezone.now()

        if data["open_at"] < now:
            raise serializers.ValidationError(
                {"open_at": ["시작 시간은 현재 시간 이후여야 합니다."]}
            )
        if data["close_at"] < now:
            raise serializers.ValidationError(
                {"close_at": ["종료 시간은 현재 시간 이후여야 합니다."]}
            )
        if data["open_at"] >= data["close_at"]:
            raise serializers.ValidationError(
                {"open_at": ["시작 시간은 종료 시간보다 빨라야 합니다."]}
            )
        return data


class AdminExamDeploymentListSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    submit_count = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)
    exam = ExamSummarySerializer()
    subject = SubjectSummarySerializer(source="exam.subject")
    cohort = CohortSummarySerializer()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


class AdminExamDeploymentListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = AdminExamDeploymentListSerializer(many=True)


class AdminExamDeploymentListQuerySerializer(serializers.Serializer[Any]):
    subject_id = serializers.IntegerField(required=False)
    cohort_id = serializers.IntegerField(required=False)
    search_keyword = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )
    sort = serializers.ChoiceField(
        choices=["created_at", "submit_count", "avg_score"],
        required=False,
        default="created_at",
    )
    order = serializers.ChoiceField(
        choices=["asc", "desc"],
        required=False,
        default="desc",
    )
