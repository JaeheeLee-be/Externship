from typing import Any

from django.db import IntegrityError

from apps.users.models import User
from apps.users.utils.admin_exceptions import (
    AccountDuplicatePhoneError,
    AccountNotFoundError,
)


class AdminAccountUpdateService:

    @staticmethod
    def update_account(account_id: int, validated_data: dict[str, Any]) -> User:
        try:
            user = User.objects.get(pk=account_id)
        except User.DoesNotExist:
            raise AccountNotFoundError()

        for field, value in validated_data.items():
            setattr(user, field, value)

        try:
            user.save(update_fields=list(validated_data.keys()) + ["updated_at"])
        except IntegrityError:
            raise AccountDuplicatePhoneError()

        return user
