class DeploymentNotFoundError(Exception):
    def __init__(self, message: str = "배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다."):
        super().__init__(message)


class DeploymentListInvalidRequestError(Exception):
    def __init__(self, message: str = "유효하지 않은 조회 요청입니다."):
        super().__init__(message)


class DeploymentDetailInvalidRequestError(Exception):
    def __init__(self, message: str = "유효하지 않은 배포 상세 조회 요청입니다."):
        super().__init__(message)


class DeploymentUpdateInvalidRequestError(Exception):
    def __init__(self, message: str = "유효하지 않은 배포 수정 요청입니다."):
        super().__init__(message)


class DeploymentConflictError(Exception):
    def __init__(self, message: str = "동일한 조건의 배포가 이미 존재합니다."):
        super().__init__(message)


class DeploymentNoQuestionsError(Exception):
    def __init__(self, message: str = "유효하지 않은 배포 생성 요청입니다."):
        super().__init__(message)


class DeploymentDetailNotFoundError(Exception):
    def __init__(self, message: str = "해당 배포 정보를 찾을 수 없습니다."):
        super().__init__(message)


class DeploymentUpdateNotFoundError(Exception):
    def __init__(self, message: str = "수정할 배포 정보를 찾을 수 없습니다."):
        super().__init__(message)


class DeploymentDeleteInvalidRequestError(Exception):
    def __init__(self, message: str = "유효하지 않은 배포 삭제 요청입니다."):
        super().__init__(message)


class DeploymentDeleteNotFoundError(Exception):
    def __init__(self, message: str = "삭제할 배포 정보를 찾을 수 없습니다."):
        super().__init__(message)


class DeploymentDeleteConflictError(Exception):
    def __init__(self, message: str = "배포 삭제 처리 중 충돌이 발생했습니다."):
        super().__init__(message)


class DeploymentStatusInvalidRequestError(Exception):
    def __init__(self, message: str = "유효하지 않은 배포 상태 요청입니다."):
        super().__init__(message)


class DeploymentStatusNotFoundError(Exception):
    def __init__(self, message: str = "해당 배포 정보를 찾을 수 없습니다."):
        super().__init__(message)


class DeploymentStatusConflictError(Exception):
    def __init__(self, message: str = "배포 상태 변경 중 충돌이 발생했습니다."):
        super().__init__(message)
