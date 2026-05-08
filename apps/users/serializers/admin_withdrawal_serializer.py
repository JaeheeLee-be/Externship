from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.courses.models.cohort import Cohort, StatusChoices
from apps.posts.models.course import Course
from apps.users.models import User, Withdrawal


class WithdrawalListQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)
    search = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(required=False, choices=User.Role.choices)
    position = serializers.ChoiceField(required=False, choices=("TA", "OM", "LC", "ENROLLED"))
    sort = serializers.ChoiceField(required=False, choices=("latest", "oldest"))


class WithdrawalListUserSerializer(serializers.ModelSerializer[User]):
    role = serializers.ChoiceField(read_only=True, choices=User.Role.choices)
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "position", "birthday"]
        read_only_fields = fields

    def get_position(self, obj: User) -> str | None:
        return _get_position(obj)


class WithdrawalListSerializer(serializers.ModelSerializer[Withdrawal]):
    user = WithdrawalListUserSerializer(read_only=True)
    reason_display = serializers.SerializerMethodField()
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Withdrawal
        fields = ["id", "user", "reason", "reason_display", "withdrawn_at"]
        read_only_fields = fields

    def get_reason_display(self, obj: Withdrawal) -> str:
        if obj.reason == Withdrawal.Reason.NO_LONGER_NEEDED:
            return "더 이상 필요하지 않음"
        return obj.get_reason_display()


class CourseNestedSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ["id", "name", "tag"]
        read_only_fields = fields


class CohortNestedSerializer(serializers.ModelSerializer[Cohort]):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Cohort
        fields = ["id", "number", "status", "start_date", "end_date"]
        read_only_fields = fields

    def get_status(self, obj: Cohort) -> str:
        if obj.status == StatusChoices.PREPARING:
            return "PENDING"
        if obj.status == StatusChoices.FINISHED:
            return "COMPLETED"
        return obj.status


class AssignedCourseSerializer(serializers.Serializer[Any]):
    course = CourseNestedSerializer(read_only=True)
    cohort = CohortNestedSerializer(read_only=True)


class WithdrawalDetailUserSerializer(serializers.ModelSerializer[User]):
    gender = serializers.CharField(read_only=True, default="")
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    profile_img_url = serializers.CharField(read_only=True, default="")

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "gender",
            "role",
            "status",
            "profile_img_url",
            "created_at",
        ]
        read_only_fields = fields

    def get_role(self, obj: User) -> str:
        position = _get_position(obj)
        if position == "ENROLLED":
            return User.Role.STUDENT
        return position or obj.role

    def get_status(self, obj: User) -> str:
        try:
            obj.withdrawal
            return "WITHDREW"
        except Withdrawal.DoesNotExist:
            pass
        if obj.is_active:
            return "ACTIVATED"
        return "DEACTIVATED"

    def to_representation(self, instance: User) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["gender"] = data.get("gender") or ""
        data["profile_img_url"] = data.get("profile_img_url") or ""
        return data


class WithdrawalDetailSerializer(serializers.ModelSerializer[Withdrawal]):
    user = WithdrawalDetailUserSerializer(read_only=True)
    assigned_courses = serializers.SerializerMethodField()
    reason_display = serializers.SerializerMethodField()
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "user",
            "assigned_courses",
            "reason",
            "reason_display",
            "reason_detail",
            "due_date",
            "withdrawn_at",
        ]
        read_only_fields = fields

    def get_assigned_courses(self, obj: Withdrawal) -> list[dict[str, Any]]:
        if obj.user is None:
            return []

        assigned_courses: list[dict[str, Any]] = []
        for cohort_student in obj.user.cohort_students.all():
            _append_assigned_course(assigned_courses, cohort_student.cohort)
        for training_assistant in obj.user.training_assistants.all():
            _append_assigned_course(assigned_courses, training_assistant.cohort)
        for operation_manager in obj.user.operation_managers.all():
            _append_course_cohorts(assigned_courses, operation_manager.course)
        for learning_coach in obj.user.learning_coachs.all():
            _append_course_cohorts(assigned_courses, learning_coach.course)
        return assigned_courses

    def get_reason_display(self, obj: Withdrawal) -> str:
        if obj.reason == Withdrawal.Reason.NO_LONGER_NEEDED:
            return "더 이상 필요하지 않음"
        return obj.get_reason_display()


class WithdrawalListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField(read_only=True)
    next = serializers.CharField(read_only=True, allow_null=True)
    previous = serializers.CharField(read_only=True, allow_null=True)
    results = WithdrawalListSerializer(many=True, read_only=True)


class WithdrawalCancelResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField(read_only=True)


class ErrorDetailSerializer(serializers.Serializer[Any]):
    error_detail = serializers.CharField(read_only=True)


def _has_related(manager: Any) -> bool:
    return bool(manager.all())


def _get_position(user: User) -> str | None:
    if _has_related(user.training_assistants):
        return "TA"
    if _has_related(user.operation_managers):
        return "OM"
    if _has_related(user.learning_coachs):
        return "LC"
    if _has_related(user.cohort_students) or user.role == User.Role.STUDENT:
        return "ENROLLED"
    return None


def _append_assigned_course(result: list[dict[str, Any]], cohort: Cohort | None) -> None:
    if cohort is None:
        return
    result.append(AssignedCourseSerializer({"course": cohort.course, "cohort": cohort}).data)


def _append_course_cohorts(result: list[dict[str, Any]], course: Course | None) -> None:
    if course is None:
        return
    for cohort in course.cohorts.all():
        _append_assigned_course(result, cohort)
