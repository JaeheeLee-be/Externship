from __future__ import annotations

from typing import Any, Union

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import SocialUsers, User
from apps.users.services.kakao import KakaoOAuthService, KakaoUserInfo
from apps.users.services.naver import NaverOAuthService, NaverUserInfo
from apps.users.utils.social_exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotProvidedError,
    MissingAuthCodeError,
    OAuthCallbackError,
    UnsupportedProviderError,
)

_UserInfo = Union[KakaoUserInfo, NaverUserInfo]


_OAUTH_SERVICES: dict[str, Any] = {
    "kakao": KakaoOAuthService,
    "naver": NaverOAuthService,
}


class SocialAuthService:

    @classmethod
    def get_auth_url(cls, provider: str) -> str:

        service = _OAUTH_SERVICES.get(provider)
        if service is None:
            raise UnsupportedProviderError()
        return str(service.get_auth_url())

    @classmethod
    def process_user(
        cls,
        provider: str,
        code: str,
        state: str = "",
        error: str | None = None,
    ) -> dict[str, Any]:

        if error:
            raise OAuthCallbackError(error)
        if not code:
            raise MissingAuthCodeError()
        user_info = cls._get_user_info(provider, code, state)
        return cls._login_and_register(provider, user_info)

    @classmethod
    def _get_user_info(cls, provider: str, code: str, state: str = "") -> _UserInfo:

        if provider == "kakao":
            redirect_uri: str = getattr(settings, "KAKAO_REDIRECT_URI", "")
            return KakaoOAuthService.get_user_info_by_code(code, redirect_uri)

        if provider == "naver":
            return NaverOAuthService.get_user_info_by_code(code, state)

        raise UnsupportedProviderError()

    @classmethod
    def _login_and_register(cls, provider: str, user_info: _UserInfo) -> dict[str, Any]:

        try:
            social_user = SocialUsers.objects.select_related("user").get(
                provider=provider,
                provider_id=user_info.provider_id,
            )
            return cls._generate_token_result(social_user.user, is_new_user=False)
        except SocialUsers.DoesNotExist:
            pass

        if not user_info.email:
            raise EmailNotProvidedError()

        if User.objects.filter(email=user_info.email).exists():
            raise EmailAlreadyRegisteredError()

        user = cls._create_social_user(user_info)
        SocialUsers.objects.create(
            user=user,
            provider=provider,
            provider_id=user_info.provider_id,
        )
        return cls._generate_token_result(user, is_new_user=True)

    @classmethod
    def _create_social_user(cls, user_info: _UserInfo) -> User:

        user = User(
            email=user_info.email or "",
            name=user_info.name or "",
            nickname=user_info.nickname or "",
            phone_number=user_info.phone_number or "",
            profile_img_url=user_info.profile_img_url,
            gender=user_info.gender,
            birthday=user_info.birthday,
        )
        user.set_unusable_password()
        user.save()
        return user

    @classmethod
    def _generate_token_result(cls, user: User, is_new_user: bool) -> dict[str, Any]:

        refresh = RefreshToken.for_user(user)
        return {
            "is_new_user": is_new_user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
