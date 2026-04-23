import os
from urllib.parse import urlparse

from rest_framework import serializers

from apps.exams.exceptions.exam_exception import ExamTitleConflict
from apps.exams.models import Exam


class ExamListCreateSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    submit_count = serializers.IntegerField(read_only=True)
    detail_url = serializers.HyperlinkedIdentityField(view_name="exam_detail", lookup_field="pk")
    thumbnail_image_url = serializers.CharField(required=False, default="default_img_url")
    subject = serializers.IntegerField()


    def validate_title(self, value):
        queryset = Exam.objects.filter(title=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ExamTitleConflict()
        return value

    def validate_thumbnail_image_url(self, value):
        if value == "default_img_url":
            return value
        path = urlparse(value).path
        ext = os.path.splitext(path)[-1].lstrip(".").lower()
        allowed = ["jpg", "jpeg", "png", "webp"]
        if ext not in allowed:
            raise serializers.ValidationError("허용되지 않는 파일 형식입니다.")
        return value

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "subject",
            "thumbnail_image_url",
            "question_count",
            "submit_count",
            "created_at",
            "updated_at",
            "detail_url",
        ]
        read_only_fields = ["id", "question_count", "submit_count", "created_at", "updated_at", "detail_url"]
