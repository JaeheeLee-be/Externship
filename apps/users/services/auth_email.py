import secrets
import uuid
from typing import Any

from celery import shared_task  # type:ignore
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from apps.core.utils.base62 import Base62


@shared_task(bind=True, max_retries=3)  # type:ignore
def send_email_async(self: Any, email: str, subject: str, message: str) -> None:
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        raise self.retry(exc=e, countdown=10)


class EmailVerification:
    @classmethod
    def send_verification_email(cls, email: str, purpose: str) -> None:
        """
        Base64 코드 생성 후 redis 코드 3분 저장한 뒤 이메일 발송

        :param email: 유저 이메일
        :param purpose: [signup, find_password, recovery] 중 하나
        :return: 이메일 발송 성공시 True 실패시 False
        """

        # Base62 코드 생성
        code = Base62.uuid_encode(uuid.uuid4(), length=6)
        # Redis 저장
        cache_key = f"email_code_{email}"
        cache_data = {
            "code": code,
            "purpose": purpose,
        }
        # cache 저장 설정
        try:
            cache.set(cache_key, cache_data, timeout=180)
        except Exception as e:
            raise ValidationError(f"error: {e}  인증 코드 생성 중 서버 오류가 발생했습니다")

        # 이메일 발송
        subject = f"[오즈코딩스쿨] 이메일 인증 코드를 확인해 주세요"
        message = f"인증 코드 : {code} 3분 이내에 입력해 주세요"

        send_email_async(email, subject, message)

    @classmethod
    def verification_code(cls, email: str, code: str) -> str:
        """
        사용자 입력한 코드를 Redis 대조 후 일치 시 토큰을 발급

        :param email: 유저 이메일
        :param code: 인증 코드
        :return: 인증 실패시 ValidationError 성공시  토큰 발급
        """

        cache_key = f"email_code_{email}"
        cached_data = cache.get(cache_key)

        # 코드 확인
        if not cached_data or cached_data.get("code") != code:
            raise ValidationError("인증코드가 만료되거나 일치하지 않습니다")

        purpose = cached_data.get("purpose")

        cache.delete(cache_key)

        # 인증 성공시 토큰 발급
        verify_token = secrets.token_urlsafe(32)

        # 승인 토큰 캐쉬 저장 유효 10분
        token_key = f"purpose_{purpose}_verify_token_{verify_token}"
        cache.set(token_key, email, timeout=600)

        return verify_token
