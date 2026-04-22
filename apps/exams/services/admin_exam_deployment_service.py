import json
import secrets

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.exceptions import ValidationError

from apps.exams.models.exam_deployment_model import ExamDeployment

BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def create_access_code(length=8):
    while True:
        code = "".join(secrets.choice(BASE62) for _ in range(length))
        if not ExamDeployment.objects.filter(access_code=code).exists():
            return code


def create_deployment(validated_data):
    exam = validated_data["exam"]
    # TODO : cohort 추후 모델 생성 후 추가 현재 test를 위해 주석처리
    # cohort = validated_data["cohort"]
    duration_time = validated_data["duration_time"]
    open_at = validated_data["open_at"]
    close_at = validated_data["close_at"]

    access_code = create_access_code()
    questions = exam.examquestion_set.all()
    snapshot = json.loads(json.dumps(list(questions.values()), cls=DjangoJSONEncoder))
    if not snapshot:
        raise ValidationError({"detail": "문제가 등록되지 않은 시험은 배포할 수 없습니다."})

    deployment = ExamDeployment.objects.create(
        exam=exam,
        # TODO : cohort 추후 모델 생성 후 추가 현재 test를 위해 주석처리
        # cohort=cohort,
        duration_time=duration_time,
        open_at=open_at,
        close_at=close_at,
        questions_snapshot_json=snapshot,
        access_code=access_code,
        status=ExamDeployment.ExamStatus.OFF,
    )

    return deployment
