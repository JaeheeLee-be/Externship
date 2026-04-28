import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from twilio.base.exceptions import TwilioRestException  # type: ignore[import-untyped]
from twilio.rest import Client  # type: ignore[import-untyped]

from apps.users.utils.purpose_enum import SmsPurpose

User = get_user_model()


class SmsVerificationService:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    service_sid = settings.TWILIO_VERIFY_SERVICE_SID

    @classmethod
    def phone_format_change(cls, phone_number: str) -> str:
        # 01012345678 -> 1012345678
        if phone_number.startswith("+82"):
            return phone_number
        return f"+82{phone_number.lstrip('0')}"

    @classmethod
    def send_verification_sms(cls, phone_number: str, purpose: SmsPurpose) -> None:
        if purpose == SmsPurpose.SIGNUP:
            if User.objects.filter(phone_number=phone_number).exists():
                raise ValidationError("이미 등록된 전화번호 입니다")

        elif purpose == SmsPurpose.FIND_EMAIL:
            if not User.objects.filter(phone_number=phone_number).exists():
                raise ValidationError("등록된 전화번호가 아닙니다.")

        elif purpose == SmsPurpose.PHONE_CHANGE:
            if not User.objects.filter(phone_number=phone_number).exists():
                raise ValidationError("변경가능한 번호가 아닙니다")

        cache_key = f"sms_code_{phone_number}"
        # 캐시 저장 용도
        cache_data = {"purpose": purpose.value}  # type: ignore[misc]
        # cache 저장 설정
        try:
            cache.set(cache_key, cache_data, timeout=180)
        except Exception as e:
            cache.delete(cache_key)
            raise ValidationError(f"error: {e}  서버 오류가 발생했습니다")
        formatted_phone = cls.phone_format_change(phone_number)

        try:
            cls.client.verify.v2.services(cls.service_sid).verifications.create(to=formatted_phone, channel="sms")
        except TwilioRestException as e:
            cache.delete(cache_key)
            # 번호 형식이 잘못되었거나 Twilio 설정 문제 시 발생
            raise ValidationError(f"SMS 발송 실패: {e.msg}")

    @classmethod
    def verify_sms_code(cls, phone_number: str, code: str, purpose: SmsPurpose) -> str:
        """
        사용자가 입력한 코드를 Twilio에 보내서 확인하고,
        성공 시 다음 단계용 sms_token을 발급합니다.
        """
        formatted_phone = cls.phone_format_change(phone_number)
        cache_key = f"sms_code_{phone_number}"
        cached_data = cache.get(cache_key)
        if not cached_data:
            raise ValidationError("인증 코드가 만료되었거나 발급되지 않았습니다.")

        cached_purpose = cached_data.get("purpose")

        try:
            SmsPurpose(purpose)
        except ValueError:
            raise ValidationError("유효하지 않은 인증 용도입니다.")

        # purpose 검증
        if cached_purpose != purpose.value:  # type: ignore[misc]
            raise ValidationError("인증 용도가 일치하지 않습니다.")

        try:
            verification_check = cls.client.verify.v2.services(cls.service_sid).verification_checks.create(
                to=formatted_phone, code=code
            )

            # Twilio 서버에서 인증 성공('approved')
            if verification_check.status == "approved":
                sms_token = secrets.token_urlsafe(32)
                token_key = f"purpose_{purpose}_sms_verify_token_{sms_token}"
                data = {"phone_number": phone_number}
                try:
                    # Redis에 저장 (용도별로 구분하여 저장, 10분 유효)
                    cache.set(token_key, data, timeout=600)

                except Exception as e:
                    raise ValidationError(f"error: {e} 서버에 오유가 발생했습니다")

                cache.delete(cache_key)

                return sms_token

            # 인증 실패 시
            raise ValidationError("인증 코드가 일치하지 않거나 만료되었습니다.")

        except TwilioRestException as e:
            raise ValidationError(f"인증 확인 중 오류 발생: {e.msg}")
