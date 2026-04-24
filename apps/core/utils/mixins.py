from rest_framework.response import Response


class ErrorDataKeyMixin:
    def handle_exception(self, exc: Exception) -> Response:
        response = super().handle_exception(exc)
        if "detail" in response.data:
            response.data["error_detail"] = response.data.pop("detail")
        return response
