class ExamDeploymentInvalidRequestError(Exception):
    def __init__(self, message: str = "유효하지 않은 시험 응시 세션입니다."):
        super().__init__(message)


class ExamDeploymentUserNotFoundError(Exception):
    def __init__(self, message: str = "사용자 정보를 찾을 수 없습니다."):
        super().__init__(message)


class ExamDeploymentNotFoundError(Exception):
    def __init__(self, message: str = "배포 정보를 찾을 수 없습니다."):
        super().__init__(message)


class ExamDeploymentInfoNotFoundError(Exception):
    def __init__(self, message: str = "해당 시험 정보를 찾을 수 없습니다."):
        super().__init__(message)


class ExamDeploymentCodeMismatchError(Exception):
    def __init__(self, message: str = "응시 코드가 일치하지 않습니다."):
        super().__init__(message)


class ExamDeploymentNotYetOpenError(Exception):
    def __init__(self, message: str = "아직 응시할 수 없습니다."):
        super().__init__(message)


class ExamDeploymentExpiredError(Exception):
    def __init__(self, message: str = "시험이 종료되었습니다."):
        super().__init__(message)


class ExamDeploymentYetExpiredError(Exception):
    def __init__(self, message: str = "시험이 이미 종료되었습니다."):
        super().__init__(message)
