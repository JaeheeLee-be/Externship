import json
import uuid
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Avg, Count, QuerySet

from apps.core.utils.base62 import Base62
from apps.exams.exceptions.admin_exam_deployment_exception import (
    DeploymentConflictError,
    DeploymentNoQuestionsError,
    DeploymentNotFoundError,
)
from apps.exams.models.exam_deployment_model import ExamDeployment
from apps.exams.models.exam_model import Exam
from apps.posts.models import Cohort


def create_access_code(length: int = 8) -> str:
    while True:
        code = Base62.uuid_encode(uuid.uuid4(), length=length)
        if not ExamDeployment.objects.filter(access_code=code).exists():
            return code


@transaction.atomic
def create_deployment(validated_data: dict[str, Any]) -> ExamDeployment:
    exam_id = validated_data["exam_id"]
    cohort_id = validated_data["cohort_id"]

    deployment_data = validated_data.copy()
    deployment_data.pop("exam_id")
    deployment_data.pop("cohort_id")

    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        raise DeploymentNotFoundError()

    try:
        cohort = Cohort.objects.get(id=cohort_id)
    except Cohort.DoesNotExist:
        raise DeploymentNotFoundError()

    if ExamDeployment.objects.filter(exam=exam, cohort=cohort).exists():
        raise DeploymentConflictError()

    snapshot = json.loads(json.dumps(list(exam.examquestion_set.values()), cls=DjangoJSONEncoder))
    if not snapshot:
        raise DeploymentNoQuestionsError()

    access_code = create_access_code()

    deployment = ExamDeployment.objects.create(
        **deployment_data,
        exam=exam,
        cohort=cohort,
        questions_snapshot_json=snapshot,
        access_code=access_code,
    )

    return deployment


SORT_FIELD_MAP = {
    "created_at": "created_at",
    "submit_count": "submit_count",
    "avg_score": "avg_score",
}


def get_deployment_list(validated_params: dict[str, Any]) -> QuerySet[ExamDeployment]:
    subject_id = validated_params.get("subject_id")
    cohort_id = validated_params.get("cohort_id")
    search_keyword = validated_params.get("search_keyword")
    sort = validated_params.get("sort", "created_at")
    order = validated_params.get("order", "desc")

    qs = ExamDeployment.objects.select_related("exam__subject", "cohort__course")

    if subject_id:
        qs = qs.filter(exam__subject_id=subject_id)
    if cohort_id:
        qs = qs.filter(cohort_id=cohort_id)
    if search_keyword:
        qs = qs.filter(exam__title__icontains=search_keyword)

    # TODO : ExamSubmission.deployment ForeignKey에 related_name 추가 시 "examsubmission" → 해당 이름으로 변경
    qs = qs.annotate(
        submit_count=Count("examsubmission"),
        avg_score=Avg("examsubmission__score"),
    )

    sort_field = SORT_FIELD_MAP.get(sort, "created_at")

    qs = qs.order_by(f"-{sort_field}" if order == "desc" else sort_field)

    return qs
