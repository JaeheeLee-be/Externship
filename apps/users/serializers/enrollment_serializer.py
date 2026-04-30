from rest_framework import serializers

from apps.courses.models.cohort import Cohort


class EnrollmentSerializer(serializers.Serializer["EnrollmentSerializer"]):
    cohort_id = serializers.IntegerField()

    def validate_cohort_id(self, value: int) -> int:
        if not Cohort.objects.filter(id=value).exists():
            raise serializers.ValidationError("존재하지 않는 기수입니다.")
        return value
