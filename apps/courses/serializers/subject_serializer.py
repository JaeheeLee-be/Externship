from rest_framework import serializers

from apps.courses.models import Subject
from apps.posts.models import Course


class SubjectCourseSerializer(serializers.ModelSerializer[Course]):

    class Meta:
        model = Course
        fields = ("id", "name", "tag")


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


class SubjectUpdateSerializer(serializers.ModelSerializer[Subject]):

    class Meta:
        model = Subject
        fields = (
            "title",
            "thumbnail_img_url",
            "number_of_days",
            "number_of_hours",
            "status",
        )
        extra_kwargs = {field: {"required": False} for field in fields}


class SubjectListSerializer(serializers.ModelSerializer[Subject]):
    course_id = serializers.IntegerField(source="course.id")
    status = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = (
            "id",
            "course_id",
            "title",
            "status",
            "thumbnail_img_url",
        )

    def get_status(self, obj: Subject) -> str:
        return "ACTIVATED" if obj.status else "DEACTIVATED"


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
