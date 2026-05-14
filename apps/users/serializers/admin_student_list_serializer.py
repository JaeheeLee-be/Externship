from typing import Any

from rest_framework import serializers

from apps.users.models import User, Withdrawal


# cohort
class CohortInfoSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    number = serializers.IntegerField()


# course
class CourseInfoSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tag = serializers.CharField()


# 현재 진행중인 기수 + 과정 묶어서 직렬화
class InProgressCourseSerializer(serializers.Serializer[Any]):
    cohort = CohortInfoSerializer()
    course = CourseInfoSerializer()


# 수강생 목록 메인 시리얼라이저
class AdminStudentListSerializer(serializers.ModelSerializer[User]):
    status = serializers.SerializerMethodField()
    in_progress_course = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "status",
            "role",
            "in_progress_course",
            "created_at",
        ]
        read_only_fields = fields

    # SerializerMethodField는 get_<필드명> 메서드를 자동으로 찾아 호출
    def get_in_progress_course(self, obj: User) -> dict[str, Any] | None:
        # __ -> 경로 cohort__status = CohortStudents -> cohort -> status
        cohort_student = (
            obj.cohort_students.select_related("cohort__course").filter(cohort__status="IN_PROGRESS").first()
        )

        if cohort_student is None:
            return None

        # mypy None 체크 요구(cohort 필드가 nullable)
        cohort = cohort_student.cohort
        if cohort is None:
            return None

        course = cohort.course
        if course is None:
            return None

        return InProgressCourseSerializer(
            {
                "cohort": {
                    "id": cohort.id,
                    "number": cohort.number,
                },
                "course": {
                    "id": cohort.course.id,
                    "name": cohort.course.name,
                    "tag": cohort.course.tag,
                },
            }
        ).data  # json 변환 가능한 딕셔너리 반환

    def get_status(self, obj: User) -> str:
        try:
            obj.withdrawal  # withdrawal 테이블에 레코드 있으면 "WITHDREW"반환
            return "WITHDREW"
        except Withdrawal.DoesNotExist:
            pass
        if obj.is_active:
            return "ACTIVATED"
        return "DEACTIVATED"
