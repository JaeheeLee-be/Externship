from __future__ import annotations


class WithdrawalError(Exception):
    pass


# 400 Bad Request 계열
class WithdrawalBadRequestError(WithdrawalError):
    pass


class AlreadyWithdrawnError(WithdrawalBadRequestError):
    def __init__(self) -> None:
        super().__init__("이미 탈퇴 신청한 계정입니다.")


class AlreadyActiveError(WithdrawalBadRequestError):
    def __init__(self) -> None:
        super().__init__("이미 활성화된 계정입니다.")


class InvalidRecoveryTokenError(WithdrawalBadRequestError):
    def __init__(self) -> None:
        super().__init__("유효하지 않은 복구 토큰입니다.")


class RecoveryPeriodExpiredError(WithdrawalBadRequestError):
    def __init__(self) -> None:
        super().__init__("복구 가능 기간이 지났습니다.")


# 404 Not Found 계열
class WithdrawalNotFoundError(WithdrawalError):
    pass


class WithdrawalRecordNotFoundError(WithdrawalNotFoundError):
    def __init__(self) -> None:
        super().__init__("탈퇴 신청 내역이 없습니다.")


class DeletedUserError(WithdrawalNotFoundError):
    def __init__(self) -> None:
        super().__init__("이미 삭제된 계정입니다.")
