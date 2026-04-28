from rest_framework.response import Response
from rest_framework.views import exception_handler
from typing import Any

def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is not None and "detail" in response.data:
        response.data["error_detail"] = response.data.pop("detail")
    return response