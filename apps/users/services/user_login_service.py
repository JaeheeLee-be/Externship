import time
from typing import Tuple

from django.contrib.auth.models import AbstractBaseUser
from django.core.cache import cache
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.utils.user_exceptions import (
    InactiveError,
    InvalidLoginError,
    WithdrawnError,
)


class UserLoginService:
    @staticmethod
    def verify_user(email: str, password: str) -> User:
        """이메일과 비밀번호를 검증하고 유저 객체를 반환."""
        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            raise InvalidLoginError()

        # 1:1 관계 데이터 조회
        if hasattr(user, "withdrawal") and user.withdrawal is not None:
            raise WithdrawnError(due_date=user.withdrawal.due_date)

        if not getattr(user, "is_active", False):
            raise InactiveError()

        return user

    @staticmethod
    def generate_token_pair(user: AbstractBaseUser) -> Tuple[str, str]:
        """유저 Access Token과 Refresh Token을 생성"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    @staticmethod
    def add_to_blacklist(refresh_token_str: str) -> bool:
        """Redis 캐시에 토큰을 블랙리스트에 등록"""
        try:
            token = RefreshToken(refresh_token_str)  # type: ignore[arg-type]
            jti = token.payload.get("jti")
            exp = token.payload.get("exp")
            now = int(time.time())
            if not isinstance(exp, int) or not isinstance(jti, str):
                return True
            timeout = exp - now
            if timeout > 0:
                cache.set(f"blacklist_{jti}", "true", timeout)
            return True
        except TokenError:
            return True

    @staticmethod
    def is_blacklisted(refresh_token_str: str) -> bool:
        """토큰이 블랙리스트에 존재하는지 캐시를 확인"""
        token = RefreshToken(refresh_token_str)  # type: ignore[arg-type]
        jti = token.payload.get("jti")
        return cache.get(f"blacklist_{jti}") is not None
