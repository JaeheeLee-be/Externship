import os
from urllib.parse import urlparse

from rest_framework import serializers

from apps.exams.models import Exam, ExamQuestion
from apps.posts.models import Subject


class ExamListSerializer(serializers.ModelSerializer[Exam]):
    question_count = serializers.IntegerField(read_only=True)
    submit_count = serializers.IntegerField(read_only=True)
    subject_name = serializers.CharField(source="subject.title", read_only=True)
    # TODO: 디테일 제작 후 주석 해제
    # detail_url = serializers.HyperlinkedIdentityField(view_name="exam-detail", lookup_field="pk")

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
            # "detail_url", 디테일 만든 후 주석 해제
        ]
        read_only_fields = [
            "id",
            "title",
            "subject_name",
            "question_count",
            "submit_count",
            "created_at",
            "updated_at",
            # "detail_url", 디테일 만든 후 주석 해제
        ]


class ExamCreateSerializer(serializers.ModelSerializer[Exam]):
    subject_id = serializers.IntegerField()
    thumbnail_image_url = serializers.CharField(required=False, default="default_img_url")

    def validate_thumbnail_image_url(self, value: str) -> str:
        if value == "default_img_url":
            return value
        path = urlparse(value).path
        ext = os.path.splitext(path)[-1].lstrip(".").lower()
        allowed = ["jpg", "jpeg", "png", "webp", "gif"]
        if ext not in allowed:
            raise serializers.ValidationError("허용되지 않는 파일 형식입니다.")
        return value

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


class SubjectNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "title"]


class QuestionNestedSerializer(serializers.ModelSerializer):
    options = serializers.ListField(source="options_json")
    correct_answer = serializers.JSONField(source="answer")

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


class ExamErrorSerializer(serializers.Serializer):
    error_detail = serializers.CharField()
