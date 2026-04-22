from rest_framework import status
from rest_framework.exceptions import APIException


class ExamTitleConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "동일한 이름의 시험이 이미 존재합니다."
    default_code = "exam_title_exists"


class SubjectNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "해당 과목 정보를 찾을 수 없습니다."
    default_code = "subject_not_found"
