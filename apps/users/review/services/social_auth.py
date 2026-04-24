from __future__ import annotations

from typing import Any, Union

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import SocialUsers, User
from apps.users.services.kakao import KakaoOAuthService, KakaoUserInfo
from apps.users.services.naver import NaverOAuthService, NaverUserInfo


class SocialAuthError(Exception):
    """소셜 인증 관련 도메인 오류"""

    pass


_UserInfo = Union[KakaoUserInfo, NaverUserInfo]


class SocialAuthService:
    """
    소셜 로그인 / 회원가입 전체 비즈니스 로직

    공개 인터페이스
    ─────────────────────────────────────────────────────────────────
    get_auth_url(provider)              → OAuth 인증 페이지 URL 반환
    process_user(provider, code, state) → 로그인 또는 회원가입 후 JWT 반환

    process_user 내부 처리 순서
    ─────────────────────────────────────────────────────────────────
    1. provider API 호출 → 소셜 유저 정보 획득         (_get_user_info)
       - kakao: settings.KAKAO_REDIRECT_URI (고정 설정값, 서비스 내부에서 직접 읽음)
       - naver: state (요청마다 달라지는 동적 값, Naver 콜백 쿼리에서 추출해 전달)
    2. 기존 소셜 유저 확인                             (_login_and_register)
       └─ 존재하면 → JWT 발급 후 반환  (is_new_user=False)
    3. 동일 이메일의 일반 이메일 유저 확인
       └─ 존재하면 → SocialAuthError("일반 이메일로 회원 가입한 유저 입니다")
    4. 신규 유저 → User + SocialUsers 생성 후 JWT 발급 (is_new_user=True)
    ─────────────────────────────────────────────────────────────────
    """

    # ── 공개 메서드 ────────────────────────────────────────────────

    @classmethod
    def get_auth_url(cls, provider: str) -> str:
        """
        provider에 맞는 OAuth 인증 페이지 URL을 반환한다.

        Raises:
            SocialAuthError: 지원하지 않는 provider
        """
        if provider == "kakao":
            return KakaoOAuthService.get_auth_url()

        if provider == "naver":
            return NaverOAuthService.get_auth_url()

        raise SocialAuthError(f"지원하지 않는 소셜 로그인 제공자입니다: {provider}")

    @classmethod
    def process_user(cls, provider: str, code: str, state: str = "") -> dict[str, Any]:
        """
        OAuth 인가 코드를 받아 로그인 또는 회원가입을 처리한 뒤 JWT를 반환한다.

        Args:
            provider : 'kakao' 또는 'naver'
            code     : OAuth 인가 코드
            state    : Naver 콜백 쿼리의 state 값 (Naver 전용 동적 값, kakao는 사용 안 함)

        Returns:
            {
                "is_new_user": bool,
                "access" : str,   # JWT access token
                "refresh": str,   # JWT refresh token
            }

        Raises:
            SocialAuthError: 지원하지 않는 provider, 인증 실패,
                             또는 일반 이메일로 가입된 유저가 소셜 로그인 시도 시
        """
        user_info = cls._get_user_info(provider, code, state)
        return cls._login_and_register(provider, user_info)

    # ── provider API 호출 ──────────────────────────────────────────

    @classmethod
    def _get_user_info(cls, provider: str, code: str, state: str = "") -> _UserInfo:
        """
        provider에 맞는 OAuth API를 호출해 소셜 유저 정보를 반환한다.

        kakao: redirect_uri는 고정 설정값이므로 settings에서 직접 읽는다.
        naver: redirect_uri는 NaverOAuthService 내부에서 settings를 읽고,
               state는 요청마다 달라지는 동적 값(Naver 콜백 쿼리 파라미터)이므로 인자로 받는다.

        Raises:
            SocialAuthError: 지원하지 않는 provider
        """
        if provider == "kakao":
            redirect_uri: str = getattr(settings, "KAKAO_REDIRECT_URI", "")
            return KakaoOAuthService.get_user_info_by_code(code, redirect_uri)

        if provider == "naver":
            return NaverOAuthService.get_user_info_by_code(code, state)

        raise SocialAuthError(f"지원하지 않는 소셜 로그인 제공자입니다: {provider}")

    # ── DB 조회 / 생성 ─────────────────────────────────────────────

    @classmethod
    def _login_and_register(cls, provider: str, user_info: _UserInfo) -> dict[str, Any]:
        """
        1. 기존 소셜 유저  → 바로 로그인
        2. 일반 이메일 유저 → SocialAuthError
        3. 신규 유저       → 회원가입 후 로그인
        """
        # 1. 기존 소셜 유저 확인
        try:
            social_user = SocialUsers.objects.select_related("user").get(
                provider=provider,
                provider_id=user_info.provider_id,
            )
            return cls._generate_token_result(social_user.user, is_new_user=False)
        except SocialUsers.DoesNotExist:
            pass

        # 2. 동일 이메일의 일반 이메일 가입 유저 확인
        if user_info.email and User.objects.filter(email=user_info.email).exists():
            raise SocialAuthError("일반 이메일로 회원 가입한 유저 입니다")

        # 3. 신규 유저 생성
        user = cls._create_social_user(user_info)
        SocialUsers.objects.create(
            user=user,
            provider=provider,
            provider_id=user_info.provider_id,
        )
        return cls._generate_token_result(user, is_new_user=True)

    # ── 헬퍼 ──────────────────────────────────────────────────────

    @classmethod
    def _create_social_user(cls, user_info: _UserInfo) -> User:
        """소셜 전용 User 생성. 비밀번호를 unusable로 설정해 일반 로그인을 차단한다."""
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
        """JWT access / refresh 토큰을 생성하고 결과 딕셔너리를 반환한다."""
        refresh = RefreshToken.for_user(user)
        return {
            "is_new_user": is_new_user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
