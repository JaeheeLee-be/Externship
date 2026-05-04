class NotAuthenticatedError(Exception):
    def __init__(self) -> None:
        super().__init__("자격 인증 데이터가 제공되지 않았습니다.")


class DuplicateNicknameError(Exception):
    def __init__(self) -> None:
        super().__init__("중복된 닉네임이 존재합니다.")


class ConflictError(Exception):
    def __init__(self, message :str="이미 중복된 회원 가입 내역이 존재 합니다.") -> None:
        super().__init__(message)
