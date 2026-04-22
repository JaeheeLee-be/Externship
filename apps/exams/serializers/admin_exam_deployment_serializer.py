from rest_framework import serializers

from apps.exams.models.exam_deployment_model import ExamDeployment


class ExamDeploymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamDeployment
        fields = [
            "exam",
            # TODO : cohort 추후 모델 생성 후 추가 현재 test를 위해 주석처리
            # "cohort",
            "duration_time",
            "open_at",
            "close_at",
        ]

    def validate(self, data):
        if data["open_at"] >= data["close_at"]:
            raise serializers.ValidationError({"open_at": "시작 시간은 종료 시간보다 빠를 수 없습니다."})

        return data
