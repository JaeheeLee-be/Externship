# 카카오/네이버 공통 로직
# 카카오/네이버 모두 필수 항목 전부 받아와서 바로 회원가입

from __future__ import annotations

from typing import Any, Optional

from django.db import IntegrityError, transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import SocialUsers, User


class SocialAuthError(Exception):
    pass


class SocialAuthService:
    """소셜 로그인/회원가입 공통 서비스"""

    @staticmethod
    def _issue_jwt(user: User) -> dict[str, str]:
        """JWT 발급"""
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def _make_placeholder_email(provider: str, provider_id: str) -> str:
        """소셜 유저 이메일 없을 시 사용할 이메일"""
        return f"{provider}_{provider_id}@social.invaild"

    @staticmethod
    def _make_placeholder_phone(provider: str, provider_id: str) -> str:
        """소셜 유저의 전화번호 없을 시 사용할 전화번호"""
        return f"S{provider_id[:19]}"[:20]

    @staticmethod
    def login_or_register(
        provider: str,
        provider_id: str,
        email: Optional[str],
        name: Optional[str],
        nickname: Optional[str],
        profile_img_url: Optional[str],
        phone_number: Optional[str],
        gender: Optional[str],
        birthday: Optional[str],
    ) -> dict[str, Any]:
        """카카오 / 네이버 소셜 유저 로그인 / 회원가입
        is_new_user: 신규 가입 여부
        access : JWT access 토큰
        refresh : JWT로 토큰 받고 view에서 쿠키로 변환
        """
        # ── 기존 소셜 유저 조회 ──────────────────────────────────
        social_user = (
            SocialUsers.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )
        if social_user:
            return {"is_new_user": False, **SocialAuthService._issue_jwt(social_user.user)}

        # ── 신규 유저 생성 ────────────────────────────────────────
        # unique 필드에 빈 문자열 말고 플레이스 홀더 사용
        resolved_email = email or SocialAuthService._make_placeholder_email(provider, provider_id)
        resolved_nickname = nickname or ""  # 닉네임은 provider 제공값 그대로 사용 (unique 제약은 모델에서 처리)
        resolved_phone = phone_number or SocialAuthService._make_placeholder_phone(provider, provider_id)
        resolved_name = name or ""

        try:
            with transaction.atomic():
                # 이미 같은 이메일로 일반 가입된 유저가 있는지 확인
                existing_user = User.objects.filter(email=resolved_email).first()

                if existing_user:
                    # 이미 존재하는 이메일이면 SocialUsers만 연결 (중복 생성 방지)
                    SocialUsers.objects.get_or_create(
                        user=existing_user,
                        provider=provider,
                        provider_id=provider_id,
                    )
                    return {"is_new_user": False, **SocialAuthService._issue_jwt(existing_user)}

                user = User(
                    email=resolved_email,
                    name=resolved_name,
                    nickname=resolved_nickname,
                    phone_number=resolved_phone,
                    gender=gender,
                    birthday=birthday,
                    profile_img_url=profile_img_url,
                    is_active=True,
                )
                user.set_unusable_password()
                user.save()

                SocialUsers.objects.create(
                    user=user,
                    provider=provider,
                    provider_id=provider_id,
                )

        except IntegrityError:
            # 동시 요청으로 먼저 생성된 경우 재조회
            social_user = (
                SocialUsers.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
            )
            if social_user:
                return {"is_new_user": False, **SocialAuthService._issue_jwt(social_user.user)}
            # 재조회에도 없으면 찐 오류
            raise SocialAuthError("소셜 유저 생성 중 오류가 발생했습니다.") from None

        return {"is_new_user": True, **SocialAuthService._issue_jwt(user)}
