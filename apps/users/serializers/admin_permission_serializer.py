from typing import Any

from rest_framework import serializers


class AdminPermissionSerializer(serializers.Serializer[Any]):
    ROLES = ["USER", "STUDENT", "ADMIN", "TA", "OM", "LC"]

    role = serializers.ChoiceField(choices=ROLES)
    cohort_id = serializers.IntegerField(required=False, allow_null=True)
    # 리스트로 받아올때: ListField
    # child: 리스트 안 원소 타입 지정
    assigned_courses = serializers.ListField(child=serializers.IntegerField(), required=False)

    # validate_<field>()는 각 필드 초기 처리 단계에서 개별적으로 수행된다.
    # 반면 validate(attrs)는 모든 필드가 검증을 통과한 뒤 마지막에 실행된다.
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        role = attrs.get("role")
        cohort_id = attrs.get("cohort_id")
        assigned_courses = attrs.get("assigned_courses")

        # TA, STUDENT는 cohort_id 필수
        if role in ["TA", "STUDENT"] and not cohort_id:
            raise serializers.ValidationError({"cohort_id": f"{role}로 권한 변경 시 필수 필드입니다."})

        # OM, LC는 assigned_courses 필수
        if role in ["OM", "LC"] and not assigned_courses:
            raise serializers.ValidationError({"assigned_courses": f"{role}로 권한 변경 시 필수 필드입니다."})

        return attrs
