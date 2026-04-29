from rest_framework import serializers

from apps.posts.models import Course, Subject


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


