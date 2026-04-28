class ExamQuestionCreateNotFound(Exception):
    def __init__(self, message: str = "생성하려는 문제 정보를 찾을 수 없습니다."):
        super().__init__(message)


class ExamQuestionCreateConflict(Exception):
    def __init__(self, message: str = "해당 쪽지시험에 등록 가능한 문제 수 또는 총 배점을 초과했습니다."):
        super().__init__(message)


class ExamQuestionUpdateNotFound(Exception):
    def __init__(self, message: str = "수정하려는 문제 정보를 찾을 수 없습니다."):
        super().__init__(message)


class ExamQuestionUpdateConflict(Exception):
    def __init__(self, message: str = "시험 문제 수 제한 또는 총 배점을 초과하여 문제를 수정할 수 없습니다."):
        super().__init__(message)
