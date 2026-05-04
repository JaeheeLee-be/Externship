from rest_framework import status
from rest_framework.exceptions import APIException, NotFound


class SubjectNotFoundError(NotFound):
    default_detail = "해당 과목을 찾을 수 없습니다."


class SubjectDuplicateTitleError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "동일한 이름의 과목이 이미 존재합니다."


class CourseNotFoundError(NotFound):
    default_detail = "해당 과정을 찾을 수 없습니다."
