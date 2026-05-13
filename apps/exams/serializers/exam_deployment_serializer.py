import json
from typing import Any

from rest_framework import serializers

from apps.courses.models.subject import Subject
from apps.exams.models.exam_model import Exam


class ExamDeploymentPathSerializer(serializers.Serializer[Any]):
    deployment_id = serializers.IntegerField(min_value=1)


class SubjectSummarySerializer(serializers.ModelSerializer[Subject]):
    class Meta:
        model = Subject
        fields = ["id", "title", "thumbnail_img_url"]


class ExamSummarySerializer(serializers.ModelSerializer[Exam]):
    subject = SubjectSummarySerializer()

    class Meta:
        model = Exam
        fields = ["id", "title", "thumbnail_img_url", "subject"]


class ExamDeploymentListQuerySerializer(serializers.Serializer[Any]):
    status = serializers.ChoiceField(
        choices=["all", "done", "pending"],
        required=False,
        default="all",
    )


class ExamDeploymentListSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    submission_id = serializers.IntegerField(allow_null=True)
    exam = ExamSummarySerializer()
    question_count = serializers.IntegerField()
    total_score = serializers.IntegerField()
    exam_info = serializers.DictField()
    is_done = serializers.BooleanField()
    duration_time = serializers.IntegerField()


class ExamDeploymentQuestionSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField(source="id")
    number = serializers.IntegerField()
    type = serializers.CharField()
    question = serializers.CharField()
    point = serializers.IntegerField()
    prompt = serializers.CharField(allow_null=True)
    blank_count = serializers.IntegerField(allow_null=True)
    options = serializers.SerializerMethodField()
    answer_input = serializers.SerializerMethodField()

    def get_options(self, obj: Any) -> list[Any] | None:
        if obj.get("options_json"):
            return list(json.loads(obj["options_json"]))
        return None

    def get_answer_input(self, obj: Any) -> Any:
        answer_json = self.context.get("answer_json", {})
        return answer_json.get(str(obj["id"]))


class ExamDeploymentCheckSerializer(serializers.Serializer[Any]):
    code = serializers.CharField()


class ExamDeploymentDetailSerializer(serializers.Serializer[Any]):
    exam_id = serializers.IntegerField(source="exam.id")
    exam_title = serializers.CharField(source="exam.title")
    duration_time = serializers.IntegerField()
    elapsed_time = serializers.IntegerField()
    cheating_count = serializers.IntegerField()
    questions = ExamDeploymentQuestionSerializer(many=True, source="questions_snapshot_json")


class ExamDeploymentStatusSerializer(serializers.Serializer[Any]):
    exam_status = serializers.CharField()
    force_submit = serializers.BooleanField()
