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


class ParentNotFoundException(NotFoundException):
    default_message = "부모 카테고리를 찾을 수 없습니다."


class DuplicateCategoryException(ConflictException):
    default_message = "동일한 이름의 카테고리가 이미 존재합니다."


class LargeHasParentException(BaseCustomException):
    status_code = 400
    default_message = "대분류는 parent_id를 가질 수 없습니다."


class InvalidMiddleParentException(BaseCustomException):
    status_code = 400
    default_message = "중분류의 부모는 대분류여야 합니다."


class InvalidSmallParentException(BaseCustomException):
    status_code = 400
    default_message = "소분류의 부모는 중분류여야 합니다."
