from typing import Any

from rest_framework import serializers

class AdminExamDeploymentCreateSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    cohort_id = serializers.IntegerField()
    duration_time = serializers.IntegerField(default=60)
    open_at = serializers.DateTimeField()
    close_at = serializers.DateTimeField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if data["open_at"] >= data["close_at"]:
            raise serializers.ValidationError({"open_at": "시작 시간은 종료 시간보다 빠를 수 없습니다."})

        return data