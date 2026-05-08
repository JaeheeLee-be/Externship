from typing import Any

from django.db import transaction

from apps.users.models import (
    CohortStudents,
    LearningCoachs,
    OperationManagers,
    TrainigAssistants,
    User,
)
from apps.users.utils.user_exceptions import UserNotFoundError


# 기존 테이블 정보 삭제와 role 정보 추가를 하나의 작업 단위로 묶음
@transaction.atomic
def update_user_role(account_id: int, validated_data: dict[str, Any]) -> User:

    # 유저 존재 여부(select_for_update: 수정하는동안 다른사람 못건그리게 잠금)
    try:
        user = User.objects.select_for_update().get(id=account_id)
    except User.DoesNotExist:
        raise UserNotFoundError()

    role = validated_data["role"]

    # 기존 테이블 정보 삭제
    tables_to_clear: list[Any] = [CohortStudents, OperationManagers, LearningCoachs, TrainigAssistants]
    for table in tables_to_clear:
        table.objects.filter(user=user).delete()

    # 변경된 role 정보 추가
    if role == "STUDENT":
        CohortStudents.objects.create(user=user, cohort_id=validated_data["cohort_id"])

    elif role == "TA":
        TrainigAssistants.objects.create(user=user, cohort_id=validated_data["cohort_id"])

    elif role == "OM":
        for course_id in validated_data["assigned_courses"]:
            OperationManagers.objects.create(user=user, course_id=course_id)

    elif role == "LC":
        for course_id in validated_data["assigned_courses"]:
            LearningCoachs.objects.create(user=user, course_id=course_id)

    # role 변경 로직
    user.role = role
    user.save()

    return user
