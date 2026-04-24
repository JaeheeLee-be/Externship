class ExamTitleConflict(Exception):
    def __init__(self, message: str = "동일한 이름의 시험이 이미 존재합니다."):
        super().__init__(message)


class SubjectNotFound(Exception):
    def __init__(self, message: str = "해당 과목 정보를 찾을 수 없습니다."):
        super().__init__(message)
