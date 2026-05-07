from typing import Any

from django.core.cache import cache
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.users.models import User
from apps.users.utils.purpose_enum import AuthPurpose

FIND_PASSWORD = AuthPurpose.FIND_PASSWORD.value


def find_password_service(validated_data: dict[str, Any]) -> None:
    """
    이메일 인증 토큰을 받아 redis cache에
    저장된 email,purpose꺼내서 유저 정보 확인후
    새 비밀번호 업데이트
    """

    email_token = validated_data["email_token"]
    new_password = validated_data["new_password"]

    email_key = f"email_verify_token_{email_token}"
    # 캐쉬에 저장된 용도, 이메일
    email_data = cache.get(email_key)

    # 토큰 유효한지 확인
    if not email_data:
        raise ValidationError("유효하지 않거나 만료된 인증 토큰입니다.")

    if FIND_PASSWORD != email_data.get("purpose"):
        raise ValidationError("유효하지 않거나 만료된 인증 토큰입니다.")
    email = email_data.get("email")

    # 비밀번호 재설정
    try:
        with transaction.atomic():
            # 동시성 제어
            user = User.objects.select_for_update().get(email=email)
            if user.check_password(new_password):
                raise ValidationError("기존 비밀번호와 동일한 비밀번호로 변경할 수 없습니다.")
            user.set_password(new_password)
            user.save()

            cache.delete(email_key)

    # 동록된 이메일이 아닐경우
    except User.DoesNotExist:
        raise ValidationError("해당 이메일을 가진 사용자를 찾을 수 없습니다.")
