from rest_framework.response import Response


class ErrorDataKeyMixin:
    """
    상속받으면 에러 키 값을 detail에서 error_detail로 변경합니다.
    (ErrorDataKeyMixin, APIView) 이런식으로 넣어주세요
    """

    def handle_exception(self, exc: Exception) -> Response:
        response: Response = super().handle_exception(exc)  # type: ignore[misc]
        if "detail" in response.data:
            response.data["error_detail"] = response.data.pop("detail")
        return response
