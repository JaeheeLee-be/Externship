from typing import Any

from rest_framework import serializers

from apps.courses.models import Subject
from apps.posts.models import Course


class SubjectCourseSerializer(serializers.ModelSerializer[Course]):

    class Meta:
        model = Course
        fields = ("id", "name", "tag")


class SubjectListSerializer(serializers.ModelSerializer[Subject]):
    course_id = serializers.IntegerField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = (
            "id",
            "course_id",
            "title",
            "thumbnail_img_url",
            "status",
        )

    def get_status(self, obj: Subject) -> str:
        return "ACTIVATED" if obj.status else "DEACTIVATED"


class SubjectCreateSerializer(serializers.ModelSerializer[Subject]):
    id = serializers.IntegerField(read_only=True)
    course_id = serializers.IntegerField()

    class Meta:
        model = Subject
        fields = (
            "id",
            "course_id",
            "title",
            "number_of_days",
            "number_of_hours",
            "thumbnail_img_url",
            "status",
        )


class SubjectDetailSerializer(serializers.ModelSerializer[Subject]):
    course = SubjectCourseSerializer(read_only=True)

    class Meta:
        model = Subject
        fields = (
            "id",
            "course",
            "title",
            "number_of_days",
            "number_of_hours",
            "thumbnail_img_url",
            "status",
            "created_at",
            "updated_at",
        )


class SubjectUpdateSerializer(serializers.ModelSerializer[Subject]):
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
        required=False,
    )

    class Meta:
        model = Subject
        fields = (
            "id",
            "course_id",
            "title",
            "number_of_days",
            "number_of_hours",
            "thumbnail_img_url",
            "status",
        )
        extra_kwargs = {
            "title": {"required": False},
            "number_of_days": {"required": False},
            "number_of_hours": {"required": False},
            "thumbnail_img_url": {"required": False},
            "status": {"required": False},
        }
        validators: list[Any] = []
