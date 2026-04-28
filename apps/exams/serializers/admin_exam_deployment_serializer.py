from typing import Any

from rest_framework import serializers

from apps.exams.models.exam_model import Exam
from apps.posts.models.cohort import Cohort
from apps.posts.models.course import Course
from apps.posts.models.subject import Subject


class SubjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "title"]


class ExamSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "title", "thumbnail_img_url"]


class CourseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "tag"]


class CohortSummarySerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer()
    display = serializers.SerializerMethodField()

    def get_display(self, obj: Cohort) -> str:
        return f"{obj.course.name} {obj.number}기"

    class Meta:
        model = Cohort
        fields = ["id", "number", "display", "course"]


class AdminExamDeploymentCreateSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    cohort_id = serializers.IntegerField()
    duration_time = serializers.IntegerField(default=60)
    open_at = serializers.DateTimeField()
    close_at = serializers.DateTimeField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if data["open_at"] >= data["close_at"]:
            raise serializers.ValidationError({"open_at": "시작 시간은 종료 시간보다 빠를 수 없습니다."})

        return data


class AdminExamDeploymentListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    submit_count = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)
    exam = ExamSummarySerializer()
    subject = SubjectSummarySerializer(source="exam.subject")
    cohort = CohortSummarySerializer()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


class AdminExamDeploymentListQuerySerializer(serializers.Serializer):
    subject_id = serializers.IntegerField(required=False)
    cohort_id = serializers.IntegerField(required=False)
    search_keyword = serializers.CharField(required=False)
    sort = serializers.ChoiceField(choices=["created_at", "submit_count", "avg_score"], default="created_at")
    order = serializers.ChoiceField(choices=["asc", "desc"], default="desc")
