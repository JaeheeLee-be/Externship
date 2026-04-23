from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

from apps.users.services.kakao import KakaoOAuthService, KakaoUserInfo
from apps.users.services.naver import NaverOAuthService, NaverUserInfo
from apps.users.services.social_auth import SocialAuthError, SocialAuthService

logger = logging.getLogger(__name__)

# provider 이름 → OAuthService 매핑
_OAUTH_SERVICES = {
    "kakao": KakaoOAuthService,
    "naver": NaverOAuthService,
}


class SocialLoginService:

    @staticmethod
    def login(provider: str, code: str, state: str | None = None) -> dict[str, Any]:
        """provider에 맞는 OAuth 서비스로 유저 정보를 가져온 뒤 로그인 or 회원가입 처리"""

        if provider not in _OAUTH_SERVICES:
            raise SocialAuthError(f"지원하지 않는 {provider}입니다.")
        try:
            user_info = SocialLoginService._fetch_user_info(provider, code, state)
        except (requests.RequestException, ValueError) as e:
            logger.exception(f"{provider} API 오류 {e}")
            raise SocialAuthError(f"{provider} 로그인에 실패하였습니다.") from e

        return SocialAuthService.login_or_register(
            provider=provider,
            provider_id=user_info.provider_id,
            email=user_info.email,
            name=user_info.name,
            nickname=user_info.nickname,
            profile_img_url=user_info.profile_img_url,
            phone_number=user_info.phone_number,
            gender=user_info.gender,
            birthday=user_info.birthday,
        )

    @staticmethod
    def _fetch_user_info(provider: str, code: str, state: str | None) -> KakaoUserInfo | NaverUserInfo:
        if provider == "kakao":
            redirect_uri = str(settings.KAKAO_REDIRECT_URI)
            return KakaoOAuthService.get_user_info_by_code(code, redirect_uri)
        if provider == "naver":
            if state is None:
                raise ValueError("네이버 로그인에는 state가 필요합니다.")
            return NaverOAuthService.get_user_info_by_code(code, state)
        raise ValueError(f"알 수 없는 provider: {provider}")
