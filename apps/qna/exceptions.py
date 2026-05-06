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


class CategoryNotFoundException(BaseCustomException):
    status_code = 404
    default_message = "해당 카테고리를 찾을 수 없습니다."


class DefaultCategoryDeleteException(ConflictException):
    default_message = "기본 카테고리는 삭제할 수 없습니다."


class ExternalAPIException(BaseCustomException):
    status_code = 502
    default_message = "외부 API 호출에 실패했습니다."


class ExternalAPITimeoutException(BaseCustomException):
    status_code = 504
    default_message = "외부 API 응답 시간이 초과되었습니다."


class InactiveSessionException(BaseCustomException):
    status_code = 403
    default_message = "활성화된 채팅 세션이 아닙니다."


class ConversationOverException(BaseCustomException):
    status_code = 429
    default_message = "더 필요한 질문은 질문 게시판을 이용해 주세요."


class GetInitialTimeoutException(BaseCustomException):
    status_code = 408
    default_message = "응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
