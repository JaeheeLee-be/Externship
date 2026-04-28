import secrets
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from apps.core.utils.base62 import Base62
from apps.users.utils.purpose_enum import AuthPurpose

User = get_user_model()


class EmailVerificationService:

    @classmethod
    def send_verification_email(cls, email: str, purpose: AuthPurpose) -> None:
        """
        Base62 코드 생성 후 redis 코드 3분 저장한 뒤 이메일 발송

        :param email: 유저 이메일
        :param purpose: [signup, find_password, recovery] 중 하나
        :raises ValidationError: Redis 캐시 저장 실패 시 발생
        """
        if purpose == AuthPurpose.SIGNUP:
            if User.objects.filter(email=email).exists():
                raise ValidationError("이미 가입된 이메일입니다.")

        elif purpose == AuthPurpose.FIND_PASSWORD:
            if not User.objects.filter(email=email, is_active=True).exists():
                raise ValidationError("가입되지 않은 이메일 입니다.")

        elif purpose == AuthPurpose.RECOVERY:
            if not User.objects.filter(email=email, is_active=False).exists():
                raise ValidationError("복구 가능한 계정이 없습니다")

        # Base62 코드 생성
        code = Base62.uuid_encode(uuid.uuid4(), length=6)
        # Redis 저장
        cache_key = f"email_code_{email}"
        cache_data = {"code": code, "purpose": purpose.value}  # type: ignore[misc]
        # cache 저장 설정
        try:
            cache.set(cache_key, cache_data, timeout=180)
        except Exception as e:
            raise ValidationError(f"error: {e}  인증 코드 생성 중 서버 오류가 발생했습니다")

        # 이메일 발송
        subject = f"[오즈코딩스쿨] 이메일 인증 코드를 확인해 주세요"
        message = f"인증 코드 : {code} 3분 이내에 입력해 주세요"

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

        except Exception:
            cache.delete(cache_key)
            raise ValidationError("이메일 발송 실패 했습니다")

    @classmethod
    def verification_code(cls, email: str, code: str, purpose: AuthPurpose) -> str:
        """
        사용자 입력한 코드를 Redis 대조 후 일치 시 토큰을 발급

        :param email: 유저 이메일
        :param code: 인증 코드
        :return: 인증 실패시 ValidationError 성공시  토큰 발급
        """

        cache_key = f"email_code_{email}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            raise ValidationError("인증코드가 만료되거나 발급되지 않았습니다.")

        cached_purpose = cached_data.get("purpose")

        # purpose 검증
        if cached_purpose != purpose.value:
            raise ValidationError("인증 용도가 일치하지 않습니다.")

        # 코드 확인
        if cached_data.get("code") != code:
            raise ValidationError("인증코드가 만료되거나 일치하지 않습니다.")

        # 인증 성공시 토큰 발급
        verify_token = secrets.token_urlsafe(32)

        # 승인 토큰 캐쉬 저장 유효 10분
        token_key = f"purpose_{purpose}_email_verify_token_{verify_token}"
        data = {"email": email, "purpose": purpose}

        try:
            cache.set(token_key, data, timeout=600)

        except Exception:
            raise ValidationError("토큰 발급 중 서버 오류가 발생했습니다.")

        cache.delete(cache_key)

        return verify_token
