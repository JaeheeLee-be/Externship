from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictException(APIException):
    """qna 답변 채택이 이미 존재 할때 사용할 error"""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "이미 채택된 답변이 존재합니다."
