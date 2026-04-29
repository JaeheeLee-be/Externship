from rest_framework import serializers

from apps.courses.models import Subject
from apps.posts.models import Course


class SubjectCourseSerializer(serializers.ModelSerializer[Course]):

    class Meta:
        model = Course
        fields = ("id", "name", "tag")


class SubjectCreateSerializer(serializers.ModelSerializer[Subject]):
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
    )

    class Meta:
        model = Subject
        fields = (
            "course_id",
            "title",
            "number_of_days",
            "number_of_hours",
            "thumbnail_img_url",
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


class SubjectCreateResponseSerializer(serializers.ModelSerializer[Subject]):
    course_id = serializers.IntegerField(source="course.id")

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


class SubjectListSerializer(serializers.ModelSerializer[Subject]):
    course_id = serializers.IntegerField(source="course.id")
    status = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = (
            "id",
            "course_id",
            "title",
            "number_of_days",
            "number_of_hours",
            "status",
            "thumbnail_img_url",
            "created_at",
            "updated_at",
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
