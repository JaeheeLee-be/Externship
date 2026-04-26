from rest_framework import status

# from rest_framework.exceptions import APIException


class ExamQuestionNotFound(Exception):
    def __init__(self):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.default_detail = "쪽지시험 문제 등록 권한이 없습니다."


class ExamQuestionValidationError(Exception):
    def __init__(self):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.default_detail = "유효하지 않은 문제 등록 데이터입니다."


class ExamQuestionConflict(Exception):
    def __init__(self):
        self.status_code = status.HTTP_409_CONFLICT
        self.default_detail = "해당 쪽지시험에 등록 가능한 문제 수 또는 총 배점을 초과했습니다."


class ExamQuestionUnauthorized(Exception):
    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.default_detail = "자격 인증 데이터가 제공되지 않았습니다."


class ExamQuestionForbidden(Exception):
    def __init__(self):
        self.status_code = status.HTTP_403_FORBIDDEN
        self.default_detail = "쪽지시험 문제 등록 권한이 없습니다."


#
# class ExamQuestionUnauthorized(APIException):
#     status_code = status.HTTP_401_UNAUTHORIZED
#     default_detail = "자격 인증 데이터가 제공되지 않았습니다."
#
#
# class ExamQuestionCreateForbidden(APIException):
#     status_code = status.HTTP_403_FORBIDDEN
#     default_detail = "쪽지시험"
