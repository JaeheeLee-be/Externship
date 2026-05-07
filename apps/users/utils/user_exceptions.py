from datetime import date
from typing import Optional


class DuplicateNicknameError(Exception):
    def __init__(self) -> None:
        super().__init__("중복된 닉네임이 존재합니다.")


class ConflictError(Exception):
    def __init__(self, message: str = "이미 중복된 회원 가입 내역이 존재 합니다.") -> None:
        super().__init__(message)


class InvalidLoginError(Exception):
    def __init__(self) -> None:
        super().__init__("입력한 이메일 또는 비밀번호가 잘못되었습니다.")


class WithdrawnError(Exception):
    def __init__(self, due_date: Optional[date] = None) -> None:
        self.expire_at = due_date.strftime("%Y-%m-%d") if due_date else None
        super().__init__("탈퇴 신청한 계정입니다.")


class InactiveError(Exception):
    def __init__(self) -> None:
        super().__init__("비활성된 계정입니다.")
