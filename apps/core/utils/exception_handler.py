from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict) and set(data.keys()) == {"detail"} and isinstance(data["detail"], str):
        response.data = {"error_detail": data["detail"]}
    else:
        response.data = {"error_detail": data}
    return response
