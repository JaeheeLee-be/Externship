class ExamTitleConflict(Exception):
    def __init__(self, message: str = "동일한 이름의 시험이 이미 존재합니다."):
        super().__init__(message)


class SubjectNotFound(Exception):
    def __init__(self, message: str = "해당 과목 정보를 찾을 수 없습니다."):
        super().__init__(message)


class ExamDeleteConflict(Exception):
    def __init__(self, message: str = "쪽지시험 삭제 중 충돌이 발생했습니다."):
        super().__init__(message)


class CreateBadRequest(Exception):
    def __init__(self, message: str = "유효하지 않은 시험 생성 요청입니다."):
        super().__init__(message)


class ExamBadRequest(Exception):
    def __init__(self, message: str = "유효하지 않은 요청입니다."):
        super().__init__(message)


class ExamDataBadRequest(Exception):
    def __init__(self, message: str = "유효하지 않은 요청 데이터입니다."):
        super().__init__(message)
