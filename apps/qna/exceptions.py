class BaseCustomException(Exception):
    status_code: int
    default_message: str

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)



class NotFoundException(BaseCustomException):
    status_code = 404
    default_message = "해당 질문 또는 답변을 찾을 수 없습니다."


class PermissionDeniedException(BaseCustomException):
    status_code = 403
    default_message = "권한이 없습니다."


class ConflictException(BaseCustomException):
    status_code = 409
    default_message = "이미 채택된 답변이 존재합니다."
