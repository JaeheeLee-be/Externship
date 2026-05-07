from typing import Any

from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from apps.users.models import User
from apps.users.utils.purpose_enum import SmsPurpose

FIND_EMAIL = SmsPurpose.FIND_EMAIL.value


def email_mask(email: str) -> str:

    username, domain = email.rsplit("@", 1)
    domain_name, domain_ext = domain.split(".", 1)

    # username 마스킹: 첫 글자 + '*' + 마지막 글자
    username_masked = username[0] + "*" * (len(username) - 2) + username[-1]

    # domain 마스킹: 첫 글자 + '*' + 마지막 2글자
    domain_masked = domain_name[0] + "*" * (len(domain_name) - 3) + domain_name[-2:]

    masked_email = f"{username_masked}@{domain_masked}.{domain_ext}"

    return masked_email


def find_email_service(validated_data: dict[str, Any]) -> str:
    """
    sms 인증 토큰을 받아 redis cache에
    저장된 phone_number,purpose꺼내서 유저 정보와 용도 확인후
    유저 이메일 제공
    """

    sms_token = validated_data["sms_token"]
    name = validated_data["name"]

    sms_key = f"sms_verify_token_{sms_token}"
    # 캐쉬에 저장된 용도, 이메일
    sms_data = cache.get(sms_key)

    # 토큰 유효한지 확인
    if not sms_data:
        raise ValidationError("유효하지 않거나 만료된 인증 토큰입니다.")

    if FIND_EMAIL != sms_data.get("purpose"):
        raise ValidationError("유효하지 않거나 만료된 인증 토큰입니다.")
    phone_number = sms_data.get("phone_number")

    # 이메일 조회
    try:
        user = User.objects.get(name=name, phone_number=phone_number)
        email = user.email
        cache.delete(sms_key)
        masked_email = email_mask(email)
        return masked_email

    # 동록된 전화번호와 이름이 아닐경우
    except User.DoesNotExist:
        raise ValidationError("해당 정보를 가진 사용자를 찾을 수 없습니다.")
