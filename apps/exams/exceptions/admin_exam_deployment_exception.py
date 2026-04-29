class DeploymentNotFoundError(Exception):
    def __init__(self, message: str = "배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다."):
        super().__init__(message)


class DeploymentConflictError(Exception):
    def __init__(self, message: str = "동일한 조건의 배포가 이미 존재합니다."):
        super().__init__(message)


class DeploymentNoQuestionsError(Exception):
    def __init__(self, message: str = "유효하지 않은 배포 생성 요청입니다."):
        super().__init__(message)
