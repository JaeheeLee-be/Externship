# 카카오/네이버 공통 로직
# 카카오/네이버 모두 필수 항목 전부 받아와서 바로 회원가입

from __future__ import annotations

from typing import Any, Optional

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import SocialUsers, User


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
        """
        카카오/네이버 소셜 유저 로그인/회원가입
        - 기존 유저 : JWT 반환
        - 신규 유저 : 필수 항목 받아와서 바로 회원가입 후 JWT 반환
        """
        social_user = (
            SocialUsers.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )

        if social_user:
            user = social_user.user
            return {"is_new_user": False, **SocialAuthService._issue_jwt(user)}

        # 신규 유저
        user = User(
            email=email or "",
            name=name or "",
            nickname=nickname or "",
            phone_number=phone_number or "",
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
        return {"is_new_user": True, **SocialAuthService._issue_jwt(user)}
