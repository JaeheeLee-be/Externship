class ConflictException(Exception):
    """qna 답변 채택이 이미 존재 할때 사용할 error"""

    def __init__(self, message: str = "이미 채택된 답변이 존재합니다.") -> None:
        super().__init__(message)
