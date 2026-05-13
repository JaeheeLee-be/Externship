from typing import Any

from rest_framework import serializers

from apps.courses.models.cohort import Cohort
from apps.courses.models.course import Course
from apps.users.models import StudentEnrollmentRequests, User


class EnrollmentUserSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = User
        fields = ["id", "email", "name", "birthday", "gender"]


class EnrollmentCourseSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = Course
        fields = ["id", "name", "tag"]


class EnrollmentCohortSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = Cohort
        fields = ["id", "number"]


#  응답 result
class StudentEnrollmentListSerializer(serializers.ModelSerializer[Any]):
    user = EnrollmentUserSerializer(read_only=True)
    cohort = EnrollmentCohortSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = StudentEnrollmentRequests
        fields = ["id", "user", "cohort", "course", "status", "created_at"]

    def get_course(self, obj: StudentEnrollmentRequests) -> dict[str, Any] | None:
        # cohort 객체를 통해 연관된 course 정보를 가져와 직렬화
        if obj.cohort and obj.cohort.course:
            return EnrollmentCourseSerializer(obj.cohort.course).data
        return None

    def get_status(self, obj: StudentEnrollmentRequests) -> str:
        return obj.status.upper() if obj.status else ""
