from rest_framework import status
from rest_framework.exceptions import PermissionDenied


class CommentPermissionDeniedError(PermissionDenied):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "해당 작업에 대한 권한이 없습니다."
    default_code = "permission_denied"


class SubjectNotFoundError(Exception):
    pass


class SubjectPermissionDeniedError(Exception):
    pass


class SubjectDuplicateTitleError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class CourseDeleteDeniedError(Exception):
    pass


class CourseAlreadyExistsError(Exception):
    pass
