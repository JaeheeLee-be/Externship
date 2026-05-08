from __future__ import annotations

from rest_framework import status


class AdminAccountException(Exception):

    status_code: int = status.HTTP_400_BAD_REQUEST  # 500 → 400
    default_detail: str = "알 수 없는 오류가 발생하였습니다."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class AccountNotFoundError(AdminAccountException):
    """대상 계정을 찾을 수 없을 때 (404)"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "사용자 정보를 찾을 수 없습니다."


class AccountDuplicatePhoneError(AdminAccountException):
    """휴대폰 번호 unique 제약 위반 (409)"""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "휴대폰 번호 중복으로 인하여 요청 처리에 실패하였습니다."


class AccountValidationError(AdminAccountException):
    """입력값 유효성 검사 실패 (400)"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "유효하지 않은 요청 파라미터입니다."