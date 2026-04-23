from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsRoleAdminUser(BasePermission):
    """ADMIN만 접근 가능"""

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(request.user.is_authenticated and request.user.role == "ADMIN")


class IsStudentUser(BasePermission):
    """STUDENT&ADMIN만 접근 가능"""

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(request.user.is_authenticated and request.user.role in {"STUDENT", "ADMIN"})
