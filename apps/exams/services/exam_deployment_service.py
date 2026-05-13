from typing import Any

from django.utils import timezone

from apps.exams.exceptions.exam_deployment_exception import (
    ExamDeploymentCodeMismatchError,
    ExamDeploymentExpiredError,
    ExamDeploymentInfoNotFoundError,
    ExamDeploymentNotFoundError,
    ExamDeploymentNotYetOpenError,
    ExamDeploymentUserNotFoundError,
)
from apps.exams.models import ExamDeployment, ExamSubmission
from apps.users.models import CohortStudents


def get_deployment_list_for_user(user: Any, status_filter: str) -> list[ExamDeployment]:
    if not CohortStudents.objects.filter(user=user).exists():
        raise ExamDeploymentUserNotFoundError()

    deployment = ExamDeployment.objects.filter(
        cohort__cohortstudents__user=user, status=ExamDeployment.ExamStatus.ON
    ).select_related("exam__subject")

    submission = ExamSubmission.objects.filter(deployment__in=deployment, submitter=user)

    submission_map = {s.deployment_id: s for s in submission}

    result = []
    for dep in deployment:
        sub = submission_map.get(dep.id)
        is_done = sub is not None

        if status_filter == "done" and not is_done:
            continue
        if status_filter == "pending" and is_done:
            continue

        setattr(dep, "submission_id", sub.id if sub else None)
        setattr(dep, "is_done", is_done)
        setattr(dep, "question_count", len(dep.questions_snapshot_json))
        setattr(dep, "total_score", sum(q.get("point", 0) for q in dep.questions_snapshot_json))
        setattr(
            dep,
            "exam_info",
            {
                "status": "done" if is_done else "pending",
                "score": sub.score if sub else None,
                "correct_answer_count": sub.correct_answer_count if sub else None,
            },
        )

        result.append(dep)

    return result


def check_deployment_code(user: Any, deployment_id: int, code: str) -> None:
    try:
        deployment = ExamDeployment.objects.get(id=deployment_id)
    except ExamDeployment.DoesNotExist:
        raise ExamDeploymentNotFoundError()

    if not CohortStudents.objects.filter(user=user, cohort=deployment.cohort).exists():
        raise ExamDeploymentNotFoundError()

    now = timezone.now()
    if deployment.close_at < now or deployment.status == ExamDeployment.ExamStatus.OFF:
        raise ExamDeploymentNotYetOpenError()
    if deployment.open_at > now:
        raise ExamDeploymentNotYetOpenError()

    if deployment.access_code != code:
        raise ExamDeploymentCodeMismatchError()


def get_deployment_detail_for_user(user: Any, deployment_id: int) -> tuple[ExamDeployment, dict[str, Any]]:
    try:
        deployment = ExamDeployment.objects.select_related("exam").get(id=deployment_id)
    except ExamDeployment.DoesNotExist:
        raise ExamDeploymentInfoNotFoundError()

    if not CohortStudents.objects.filter(user=user, cohort=deployment.cohort).exists():
        raise ExamDeploymentInfoNotFoundError()

    now = timezone.now()
    if deployment.close_at < now or deployment.status == ExamDeployment.ExamStatus.OFF:
        raise ExamDeploymentExpiredError()

    submission = ExamSubmission.objects.filter(deployment=deployment, submitter=user).first()

    elapsed_time = int((now - submission.started_at).total_seconds()) if submission else 0

    cheating_count = submission.cheating_count if submission else 0

    for i, question in enumerate(deployment.questions_snapshot_json):
        question["number"] = i + 1

    setattr(deployment, "elapsed_time", elapsed_time)
    setattr(deployment, "cheating_count", cheating_count)

    answer_json = submission.answer_json if submission else {}

    return deployment, answer_json


def get_deployment_status_for_user(user: Any, deployment_id: int) -> dict[str, Any]:
    try:
        deployment = ExamDeployment.objects.get(id=deployment_id)
    except ExamDeployment.DoesNotExist:
        raise ExamDeploymentInfoNotFoundError()

    if not CohortStudents.objects.filter(user=user, cohort=deployment.cohort).exists():
        raise ExamDeploymentInfoNotFoundError()

    now = timezone.now()
    is_expired = deployment.close_at < now or deployment.status == ExamDeployment.ExamStatus.OFF

    if is_expired:
        return {"exam_status": "closed", "force_submit": is_expired}

    submission = ExamSubmission.objects.filter(deployment=deployment, submitter=user).first()
    force_submit = bool(
        submission and (now - submission.started_at).total_seconds() >= deployment.duration_time * 60
    )

    return {"exam_status": "activated", "force_submit": force_submit}
