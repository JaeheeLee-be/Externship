from typing import Any

from django.core.cache import cache
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.users.models import User
from apps.users.utils.purpose_enum import SmsPurpose
from apps.users.utils.user_exceptions import ConflictError

PHONE_CHANGE = SmsPurpose.PHONE_CHANGE.value


def change_phone_service(validated_data: dict[str, Any], user: User) -> str:
    """
    sms 인증 토큰을 받아 redis cache에
    저장된 phone_number, purpose를 꺼내서 용도 확인 후
    DB에 동일한 번호가 없으면 기존 번호를 새 번호로 변경
    """
    sms_token = validated_data["phone_verify_token"]
    sms_key = f"sms_verify_token_{sms_token}"

    # 캐시에 저장된 용도, 전화번호 조회
    sms_data = cache.get(sms_key)

    # 토큰 유효성 확인
    if not sms_data:
        raise ValidationError("유효하지 않거나 만료된 인증 토큰입니다.")

    if PHONE_CHANGE != sms_data.get("purpose"):
        raise ValidationError("유효하지 않거나 만료된 인증 토큰입니다.")

    new_phone_number: str = sms_data.get("phone_number")

    # 현재 번호와 동일한지 확인
    if user.phone_number == new_phone_number:
        raise ValidationError("현재 휴대폰 번호와 동일합니다.")

    with transaction.atomic():
        # 변경 대상 유저 락
        locked_user = User.objects.select_for_update().get(pk=user.pk)

        # DB 중복 확인 (본인 번호 제외)
        if User.objects.filter(phone_number=new_phone_number).exists():
            raise ConflictError("이미 등록된 휴대폰 번호입니다.")

        # 전화번호 변경
        locked_user.phone_number = new_phone_number
        locked_user.save(update_fields=["phone_number"])

    # 사용한 토큰 즉시 삭제 (재사용 방지)
    cache.delete(sms_key)

    return new_phone_number
