from __future__ import annotations


class SocialAuthError(Exception):

    pass


class InvalidProfileImageExtensionError(Exception):

    pass


class UnsupportedProviderError(SocialAuthError):

    def __init__(self) -> None:
        super().__init__("지원하지 않는 소셜 로그인 제공자입니다.")


class OAuthCallbackError(SocialAuthError):

    def __init__(self, error: str) -> None:
        super().__init__(error)


class MissingAuthCodeError(SocialAuthError):

    def __init__(self) -> None:
        super().__init__("인가 코드(code)가 없습니다.")


class EmailNotProvidedError(SocialAuthError):

    def __init__(self) -> None:
        super().__init__("이메일 정보를 가져올 수 없습니다.")


class EmailAlreadyRegisteredError(SocialAuthError):

    def __init__(self) -> None:
        super().__init__("일반 이메일로 회원 가입한 유저 입니다")


class InternalServerError(SocialAuthError):

    def __init__(self) -> None:
        super().__init__("서버 오류가 발생했습니다.")
