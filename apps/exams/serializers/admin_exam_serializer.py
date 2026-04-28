import json
from typing import Any

from rest_framework import serializers

from apps.exams.models import Exam, ExamQuestion
from apps.posts.models import Subject


class ExamListSerializer(serializers.ModelSerializer[Exam]):
    question_count = serializers.IntegerField(read_only=True)
    submit_count = serializers.IntegerField(read_only=True)
    subject_name = serializers.CharField(source="subject.title", read_only=True)
    detail_url = serializers.HyperlinkedIdentityField(view_name="exam-detail", lookup_url_kwarg="exam_id")

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "subject_name",
            "question_count",
            "submit_count",
            "created_at",
            "updated_at",
            "detail_url",
        ]
        read_only_fields = [
            "id",
            "title",
            "subject_name",
            "question_count",
            "submit_count",
            "created_at",
            "updated_at",
            "detail_url",
        ]


class ExamCreatePutSerializer(serializers.ModelSerializer[Exam]):
    subject_id = serializers.IntegerField()
    thumbnail_image_url = serializers.CharField(required=False, default="default_img_url")

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "subject_id",
            "thumbnail_image_url",
        ]
        read_only_fields = ["id"]
        extra_kwargs: dict[str, dict[str, list[object]]] = {"title": {"validators": []}}


class SubjectNestedSerializer(serializers.ModelSerializer[Subject]):
    class Meta:
        model = Subject
        fields = ["id", "title"]


class QuestionNestedSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.SerializerMethodField()
    correct_answer = serializers.JSONField(source="answer")

    def get_options(self, obj: ExamQuestion) -> list:
        if not obj.options_json:
            return []
        return json.loads(obj.options_json)

    class Meta:
        model = ExamQuestion
        fields = ["id", "type", "question", "prompt", "point", "options", "correct_answer", "explanation"]


class ExamDetailSerializer(serializers.ModelSerializer[Exam]):
    subject = SubjectNestedSerializer(read_only=True)
    questions = QuestionNestedSerializer(many=True, read_only=True, source="examquestion_set")

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "subject",
            "questions",
            "thumbnail_image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "title",
            "subject",
            "questions",
            "thumbnail_image_url",
            "created_at",
            "updated_at",
        ]


class ExamErrorSerializer(serializers.Serializer[Any]):
    error_detail = serializers.CharField()


class ExamValidationErrorSerializer(serializers.Serializer[Any]):
    error_detail = serializers.DictField()


class ExamDeleteResponseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
