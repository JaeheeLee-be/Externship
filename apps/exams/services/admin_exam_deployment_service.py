import json
import uuid
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.exceptions import ValidationError

from apps.core.utils.base62 import Base62
from apps.exams.models.exam_deployment_model import ExamDeployment


class DeploymentConflictError(Exception):
    pass


def create_access_code(length: int = 8) -> str:
    while True:
        code = Base62.uuid_encode(uuid.uuid4(), length=length)
        if not ExamDeployment.objects.filter(access_code=code).exists():
            return code


def create_deployment(validated_data: dict[str, Any]) -> ExamDeployment:
    exam = validated_data["exam"]

    access_code = create_access_code()
    snapshot = json.loads(json.dumps(list(exam.examquestion_set.values()), cls=DjangoJSONEncoder))
    if not snapshot:
        raise ValidationError({"detail": "문제가 등록되지 않은 시험은 배포할 수 없습니다."})

    if ExamDeployment.objects.filter(exam=exam).exists():
        raise DeploymentConflictError()

    deployment = ExamDeployment.objects.create(
        **validated_data,
        questions_snapshot_json=snapshot,
        access_code=access_code,
        status=ExamDeployment.ExamStatus.OFF,
    )

    return deployment
