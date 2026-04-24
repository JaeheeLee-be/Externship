from __future__ import annotations


class SocialAuthError(Exception):
    """소셜 인증 관련 도메인 오류 (기본)"""

    pass


class UnsupportedProviderError(SocialAuthError):
    """지원하지 않는 OAuth provider"""

    def __init__(self, provider: str) -> None:
        super().__init__(f"지원하지 않는 소셜 로그인 제공자입니다: {provider}")


class EmailNotProvidedError(SocialAuthError):
    """소셜 provider로부터 이메일 정보를 받지 못한 경우"""

    def __init__(self) -> None:
        super().__init__("이메일 정보를 가져올 수 없습니다.")


class EmailAlreadyRegisteredError(SocialAuthError):
    """동일 이메일로 일반 가입된 유저가 소셜 로그인 시도"""

    def __init__(self) -> None:
        super().__init__("일반 이메일로 회원 가입한 유저 입니다")
