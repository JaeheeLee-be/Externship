from rest_framework.request import Request

from apps.users.models import User


class AuthenticatedRequest(Request):
    """test 코드를 위한 type 정리"""

    user: User
