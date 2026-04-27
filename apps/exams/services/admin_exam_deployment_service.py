import json
import uuid
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder

from apps.core.utils.base62 import Base62
# TODO : 예외 폴더 생성 후 경로 변경
from apps.exams.exceptions.exam_deploy_exceptions import (
    DeploymentConflictError,
    DeploymentNoQuestionsError,
    DeploymentNotFoundError
)
from apps.exams.models.exam_deployment_model import ExamDeployment
from apps.exams.models.exam_model import Exam
from apps.posts.models import Cohort


def create_access_code(length: int = 8) -> str:
    while True:
        code = Base62.uuid_encode(uuid.uuid4(), length=length)
        if not ExamDeployment.objects.filter(access_code=code).exists():
            return code


def create_deployment(validated_data: dict[str, Any]) -> ExamDeployment:
    exam_id = validated_data.pop("exam_id")
    cohort_id = validated_data.pop("cohort_id")

    # API명세서 상에 404 표현을 위해 모델 시리얼라이즈를 사용하지 않고 서비스에서 검증하는 방식으로 진행
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
        **validated_data,
        exam=exam,
        cohort=cohort,
        questions_snapshot_json=snapshot,
        access_code=access_code,
    )

    return deployment