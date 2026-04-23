import os
from urllib.parse import urlparse

from rest_framework import serializers

from apps.exams.exceptions.exam_exception import ExamTitleConflict
from apps.exams.models import Exam

class ExamBaseSerializer(serializers.ModelSerializer):
    pass # 중복사항 넣기위해 제작했으나 없으면 추후 삭제 예정

class ExamListCreateSerializer(ExamBaseSerializer):
    question_count = serializers.IntegerField(read_only=True)
    submit_count = serializers.IntegerField(read_only=True)
    subject_name = serializers.SerializerMethodField()
    detail_url = serializers.HyperlinkedIdentityField(view_name="exam-detail", lookup_field="pk")

    def get_subject_name(self, obj):
        return obj.subject.title

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
        read_only_fields = "__all__"

class ExamCreateSerializer(ExamBaseSerializer):
    subject_id = serializers.IntegerField()
    thumbnail_image_url = serializers.CharField(required=False, default="default_img_url")


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
        fields =[
            "id",
            "title",
            "subject_id",
            "thumbnail_image_url",
        ]
        read_only_fields = ["id"]

